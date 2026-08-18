from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.corpus.resolution import parse_identifier
from discovery.retrieval.gateway_models import IntegrityReport
from discovery.storage.models import IntegrityAssertionRow, WorkIdentifierRow


class WorkIntegrityStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_id: str
    state: str
    relations: list[str] = Field(default_factory=list)
    assertions: int = 0
    warning: str | None = None


class IntegrityService:
    _HIGH_RISK = {
        "retracts",
        "retracted_by",
        "retraction",
        "withdraws",
        "withdrawn_by",
        "withdrawal",
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    def ingest(self, report: IntegrityReport, *, work_id: str | None = None) -> int:
        resolved_work_id = work_id or self._resolve_work(report.query_identifier)
        now = datetime.now(UTC)
        count = 0
        for assertion in report.assertions:
            row_id = stable_id(
                "integrity-assertion",
                ":".join(
                    [
                        assertion.subject_identifier,
                        assertion.relation_type,
                        assertion.object_identifier or "",
                        assertion.provider,
                    ]
                ),
            )
            row = self.session.get(IntegrityAssertionRow, row_id)
            if row is None:
                row = IntegrityAssertionRow(
                    id=row_id,
                    work_id=resolved_work_id,
                    subject_identifier=assertion.subject_identifier,
                    relation_type=assertion.relation_type,
                    object_identifier=assertion.object_identifier,
                    provider=assertion.provider,
                    notice_date=assertion.notice_date,
                    status=assertion.status,
                    retrieved_at=now,
                    payload_json=assertion.payload,
                )
            else:
                row.work_id = resolved_work_id or row.work_id
                row.notice_date = assertion.notice_date
                row.status = assertion.status
                row.retrieved_at = now
                row.payload_json = assertion.payload
            self.session.add(row)
            count += 1
        self.session.flush()
        return count

    def status(self, work_id: str) -> WorkIntegrityStatus:
        rows = list(
            self.session.scalars(
                select(IntegrityAssertionRow).where(IntegrityAssertionRow.work_id == work_id)
            )
        )
        relations = sorted({row.relation_type for row in rows})
        normalized = {relation.casefold() for relation in relations}
        if normalized & self._HIGH_RISK:
            state = "attention_required"
            warning = "At least one provider reports a retraction or withdrawal relation."
        elif rows:
            state = "assertions_present"
            warning = (
                "Integrity providers report update/version assertions; absence of a retraction "
                "assertion is not clearance."
            )
        else:
            state = "unknown"
            warning = "No stored integrity assertion is not evidence of integrity clearance."
        return WorkIntegrityStatus(
            work_id=work_id,
            state=state,
            relations=relations,
            assertions=len(rows),
            warning=warning,
        )

    def _resolve_work(self, identifier_value: str) -> str | None:
        parsed = parse_identifier(identifier_value)
        if parsed is None:
            return None
        scheme, value = parsed
        row = self.session.scalar(
            select(WorkIdentifierRow).where(
                WorkIdentifierRow.scheme == scheme,
                WorkIdentifierRow.value == value,
            )
        )
        return row.work_id if row is not None else None
