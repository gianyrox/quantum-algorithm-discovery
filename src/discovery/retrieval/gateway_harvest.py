from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.models import SearchQuery
from discovery.retrieval.service import RetrievalService
from discovery.storage.models import ProviderHarvestCheckpointRow, RetrievalHitRow


class GatewayCursorHarvestPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_pages: int = Field(default=100, ge=1, le=100000)
    max_records: int | None = Field(default=None, ge=1)
    stop_on_error: bool = True


class GatewayCursorHarvestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pages: int = Field(ge=0)
    records: int = Field(ge=0)
    unique_work_ids: list[str] = Field(default_factory=list)
    next_cursor: str | None = None
    exhausted: bool = False
    cursor_ephemeral: bool | None = None
    errors: list[str] = Field(default_factory=list)


def _payload_fingerprint(payload: dict[str, object]) -> str:
    stable = {key: value for key, value in payload.items() if key != "cursor"}
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class GatewayCursorHarvestEngine:
    """Persist and resume the gateway's signed-cursor `/research/harvest` pages."""

    def __init__(self, session: Session, gateway: GatewayProvider) -> None:
        self.session = session
        self.gateway = gateway
        self.retrieval = RetrievalService(session, gateway)

    def execute(
        self,
        payload: dict[str, object],
        *,
        policy: GatewayCursorHarvestPolicy | None = None,
    ) -> GatewayCursorHarvestResult:
        resolved = policy or GatewayCursorHarvestPolicy()
        fingerprint = _payload_fingerprint(payload)
        base_payload = {key: value for key, value in payload.items() if key != "cursor"}
        raw_cursor = payload.get("cursor")
        supplied_cursor = raw_cursor if isinstance(raw_cursor, str) else None
        work_ids: set[str] = set()
        page_index, cursor, already_exhausted = self._resume_state(
            fingerprint,
            work_ids,
            supplied_cursor=supplied_cursor,
        )
        if already_exhausted:
            return GatewayCursorHarvestResult(
                pages=0,
                records=0,
                unique_work_ids=sorted(work_ids),
                next_cursor=None,
                exhausted=True,
            )

        pages = 0
        records = 0
        errors: list[str] = []
        exhausted = False
        cursor_ephemeral: bool | None = None
        while pages < resolved.max_pages:
            if resolved.max_records is not None and records >= resolved.max_records:
                break
            checkpoint = self._checkpoint(
                fingerprint,
                base_payload,
                page_index,
                cursor,
            )
            try:
                request_payload = dict(base_payload)
                if cursor is not None:
                    request_payload["cursor"] = cursor
                page = self.gateway.harvest_page(request_payload)
                provider = page.provider or str(base_payload.get("provider", "unknown"))
                wrapped = [
                    {
                        "provider": provider,
                        "provider_rank": index,
                        "raw_record": record,
                    }
                    for index, record in enumerate(page.records, start=1)
                ]
                query = SearchQuery(
                    text=checkpoint.query_text or f"gateway-harvest:{provider}",
                    limit=max(1, len(wrapped) or 1),
                    providers=[provider] if provider != "unknown" else [],
                )
                response = GatewayProvider.parse_search_response(
                    query,
                    {"data": {"results": wrapped}},
                )
                run_id = self.retrieval.record_response(
                    query,
                    response,
                    provider_name=f"gateway-harvest:{provider}",
                )
                page_work_ids = {hit.work.id for hit in response.hits if hit.work is not None}
                before = len(work_ids)
                work_ids.update(page_work_ids)
                checkpoint.status = "completed"
                checkpoint.retrieval_run_id = run_id
                checkpoint.next_cursor = page.cursor
                checkpoint.retrieved_count = len(page.records)
                checkpoint.new_unique_count = len(work_ids) - before
                checkpoint.updated_at = datetime.now(UTC)
                checkpoint.error = None
                self.session.add(checkpoint)
                self.session.flush()

                pages += 1
                records += len(page.records)
                cursor = page.cursor
                cursor_ephemeral = page.cursor_ephemeral
                exhausted = page.exhausted
                if page.exhausted or page.cursor is None:
                    break
                page_index += 1
            except Exception as exc:
                message = f"page:{page_index}:{type(exc).__name__}:{exc}"
                checkpoint.status = "failed"
                checkpoint.error = message
                checkpoint.updated_at = datetime.now(UTC)
                self.session.add(checkpoint)
                self.session.flush()
                errors.append(message)
                if resolved.stop_on_error:
                    raise
                break
        return GatewayCursorHarvestResult(
            pages=pages,
            records=records,
            unique_work_ids=sorted(work_ids),
            next_cursor=cursor,
            exhausted=exhausted,
            cursor_ephemeral=cursor_ephemeral,
            errors=errors,
        )

    def _resume_state(
        self,
        fingerprint: str,
        work_ids: set[str],
        *,
        supplied_cursor: str | None,
    ) -> tuple[int, str | None, bool]:
        rows = list(
            self.session.scalars(
                select(ProviderHarvestCheckpointRow)
                .where(
                    ProviderHarvestCheckpointRow.provider == "x402-research-gateway",
                    ProviderHarvestCheckpointRow.query_fingerprint == fingerprint,
                    ProviderHarvestCheckpointRow.status == "completed",
                )
                .order_by(ProviderHarvestCheckpointRow.page_index)
            )
        )
        if not rows:
            return 0, supplied_cursor, False
        for row in rows:
            if row.retrieval_run_id is None:
                continue
            hits = self.session.scalars(
                select(RetrievalHitRow).where(
                    RetrievalHitRow.retrieval_run_id == row.retrieval_run_id,
                    RetrievalHitRow.work_id.is_not(None),
                )
            )
            work_ids.update(hit.work_id for hit in hits if hit.work_id is not None)
        last = rows[-1]
        if last.next_cursor is None:
            return last.page_index, None, True
        return last.page_index + 1, last.next_cursor, False

    def _checkpoint(
        self,
        fingerprint: str,
        payload: dict[str, object],
        page_index: int,
        cursor: str | None,
    ) -> ProviderHarvestCheckpointRow:
        row_id = stable_id(
            "gateway-harvest-checkpoint",
            f"{fingerprint}:{page_index}",
        )
        row = self.session.get(ProviderHarvestCheckpointRow, row_id)
        if row is None:
            row = ProviderHarvestCheckpointRow(
                id=row_id,
                provider="x402-research-gateway",
                query_fingerprint=fingerprint,
                query_text=str(payload.get("query", payload.get("term", ""))),
                page_index=page_index,
                cursor_used=cursor,
                status="pending",
                retrieved_count=0,
                new_unique_count=0,
                updated_at=datetime.now(UTC),
            )
            self.session.add(row)
            self.session.flush()
        return row
