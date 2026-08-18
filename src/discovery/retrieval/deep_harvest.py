from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.retrieval.models import QueryPlan, SearchQuery
from discovery.retrieval.paging import PagedResearchProvider
from discovery.retrieval.saturation import SaturationObservation, SaturationPolicy
from discovery.retrieval.service import RetrievalService, query_fingerprint
from discovery.storage.models import ProviderHarvestCheckpointRow, RetrievalHitRow


class DeepHarvestPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_pages: int = Field(default=100, ge=1, le=100000)
    max_records: int | None = Field(default=None, ge=1)
    saturation: SaturationPolicy | None = None
    stop_on_error: bool = True


class DeepHarvestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    query: SearchQuery
    pages: int = Field(ge=0)
    hits: int = Field(ge=0)
    unique_work_ids: list[str] = Field(default_factory=list)
    exhausted: bool = False
    stopped_for_saturation: bool = False
    next_cursor: str | None = None
    observations: list[SaturationObservation] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DeepHarvestEngine:
    """Resumable provider-cursor harvesting for providers that expose pages."""

    def __init__(self, session: Session, provider: PagedResearchProvider) -> None:
        self.session = session
        self.provider = provider
        # This entire engine is retained only for v0.4-v0.10 direct-provider
        # parity tests. The active v0.11 boundary uses GatewayCursorHarvestEngine.
        self.retrieval = RetrievalService(session, provider, allow_legacy_direct=True)

    def execute(
        self,
        query: SearchQuery,
        *,
        plan: QueryPlan | None = None,
        policy: DeepHarvestPolicy | None = None,
    ) -> DeepHarvestResult:
        resolved = policy or DeepHarvestPolicy()
        fingerprint = query_fingerprint(query)
        work_ids: set[str] = set()
        observations: list[SaturationObservation] = []
        errors: list[str] = []
        page_index, cursor = self._resume_state(fingerprint, work_ids)
        pages_this_run = 0
        hits_this_run = 0
        exhausted = False
        saturated = False

        while pages_this_run < resolved.max_pages:
            if resolved.max_records is not None and hits_this_run >= resolved.max_records:
                break
            checkpoint = self._checkpoint(fingerprint, query, page_index, cursor)
            if checkpoint.status == "completed":
                cursor = checkpoint.next_cursor
                if not cursor:
                    exhausted = True
                    break
                page_index += 1
                continue
            before = len(work_ids)
            try:
                page = self.provider.search_page(
                    query,
                    cursor=cursor,
                    page_index=page_index,
                )
                run_id = self.retrieval.record_response(
                    query,
                    page.response,
                    plan=plan,
                    provider_name=self.provider.name,
                )
                page_work_ids = {
                    hit.work.id
                    for hit in page.response.hits
                    if hit.work is not None
                }
                work_ids.update(page_work_ids)
                retrieved = len(page.response.hits)
                checkpoint.status = "completed"
                checkpoint.retrieval_run_id = run_id
                checkpoint.next_cursor = page.next_cursor
                checkpoint.retrieved_count = retrieved
                checkpoint.new_unique_count = len(work_ids) - before
                checkpoint.updated_at = datetime.now(UTC)
                checkpoint.error = None
                self.session.add(checkpoint)
                self.session.flush()
                pages_this_run += 1
                hits_this_run += retrieved
                observations.append(
                    SaturationObservation(
                        iteration=page_index + 1,
                        retrieved=retrieved,
                        new_unique_works=len(work_ids) - before,
                        cumulative_unique_works=len(work_ids),
                    )
                )
                cursor = page.next_cursor
                exhausted = page.exhausted
                if resolved.saturation is not None and resolved.saturation.saturated(observations):
                    saturated = True
                    break
                if page.exhausted or not page.next_cursor:
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

        return DeepHarvestResult(
            provider=self.provider.name,
            query=query,
            pages=pages_this_run,
            hits=hits_this_run,
            unique_work_ids=sorted(work_ids),
            exhausted=exhausted,
            stopped_for_saturation=saturated,
            next_cursor=cursor,
            observations=observations,
            errors=errors,
        )

    def _resume_state(self, fingerprint: str, work_ids: set[str]) -> tuple[int, str | None]:
        rows = list(
            self.session.scalars(
                select(ProviderHarvestCheckpointRow)
                .where(
                    ProviderHarvestCheckpointRow.provider == self.provider.name,
                    ProviderHarvestCheckpointRow.query_fingerprint == fingerprint,
                    ProviderHarvestCheckpointRow.status == "completed",
                )
                .order_by(ProviderHarvestCheckpointRow.page_index)
            )
        )
        if not rows:
            return 0, None
        for row in rows:
            if row.retrieval_run_id is None:
                continue
            hit_rows = self.session.scalars(
                select(RetrievalHitRow).where(
                    RetrievalHitRow.retrieval_run_id == row.retrieval_run_id,
                    RetrievalHitRow.work_id.is_not(None),
                )
            )
            work_ids.update(hit.work_id for hit in hit_rows if hit.work_id is not None)
        last = rows[-1]
        if last.next_cursor is None:
            return last.page_index, None
        return last.page_index + 1, last.next_cursor

    def _checkpoint(
        self,
        fingerprint: str,
        query: SearchQuery,
        page_index: int,
        cursor: str | None,
    ) -> ProviderHarvestCheckpointRow:
        row_id = stable_id(
            "provider-harvest-checkpoint",
            f"{self.provider.name}:{fingerprint}:{page_index}",
        )
        row = self.session.get(ProviderHarvestCheckpointRow, row_id)
        if row is None:
            row = ProviderHarvestCheckpointRow(
                id=row_id,
                provider=self.provider.name,
                query_fingerprint=fingerprint,
                query_text=query.text,
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
