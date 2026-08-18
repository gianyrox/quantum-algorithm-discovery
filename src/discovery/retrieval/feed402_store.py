from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from discovery.retrieval.feed402 import RecordedFeed402Envelope
from discovery.storage.models import Feed402EnvelopeRow


@dataclass(frozen=True)
class Feed402PersistenceSummary:
    envelope_ids: list[str]
    envelope_count: int
    citation_count: int
    lineage_count: int
    specs: list[str]


class Feed402EnvelopeRepository:
    """Persist feed402 envelopes before downstream scientific interpretation."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def persist_retrieval_run(
        self,
        retrieval_run_id: str,
        records: list[RecordedFeed402Envelope],
        *,
        spec: str | None,
        merchant: str,
    ) -> Feed402PersistenceSummary:
        return self._persist(
            records,
            retrieval_run_id=retrieval_run_id,
            spec=spec,
            merchant=merchant,
        )

    def persist_unscoped(
        self,
        records: list[RecordedFeed402Envelope],
        *,
        spec: str | None,
        merchant: str,
    ) -> Feed402PersistenceSummary:
        return self._persist(records, spec=spec, merchant=merchant)

    def persist_campaign_run(
        self,
        campaign_run_id: str,
        records: list[RecordedFeed402Envelope],
        *,
        spec: str | None,
        merchant: str,
    ) -> Feed402PersistenceSummary:
        return self._persist(
            records,
            campaign_run_id=campaign_run_id,
            spec=spec,
            merchant=merchant,
        )

    def link_retrieval_runs_to_campaign(
        self,
        campaign_run_id: str,
        retrieval_run_ids: list[str],
    ) -> int:
        if not retrieval_run_ids:
            return 0
        envelope_ids = list(
            self.session.scalars(
                select(Feed402EnvelopeRow.id)
                .where(Feed402EnvelopeRow.retrieval_run_id.in_(retrieval_run_ids))
                .where(Feed402EnvelopeRow.campaign_run_id.is_(None))
            )
        )
        if not envelope_ids:
            return 0
        self.session.execute(
            update(Feed402EnvelopeRow)
            .where(Feed402EnvelopeRow.id.in_(envelope_ids))
            .values(campaign_run_id=campaign_run_id)
        )
        self.session.flush()
        return len(envelope_ids)

    def summarize_campaign(self, campaign_run_id: str) -> Feed402PersistenceSummary:
        rows = list(
            self.session.scalars(
                select(Feed402EnvelopeRow)
                .where(Feed402EnvelopeRow.campaign_run_id == campaign_run_id)
                .order_by(Feed402EnvelopeRow.received_at, Feed402EnvelopeRow.id)
            )
        )
        specs = sorted({row.spec for row in rows if row.spec is not None})
        return Feed402PersistenceSummary(
            envelope_ids=[row.id for row in rows],
            envelope_count=len(rows),
            citation_count=sum(row.citation_count for row in rows),
            lineage_count=sum(row.lineage_count for row in rows),
            specs=specs,
        )

    def _persist(
        self,
        records: list[RecordedFeed402Envelope],
        *,
        campaign_run_id: str | None = None,
        retrieval_run_id: str | None = None,
        spec: str | None,
        merchant: str,
    ) -> Feed402PersistenceSummary:
        ids: list[str] = []
        citation_count = 0
        lineage_count = 0
        for record in records:
            envelope = record.envelope
            first_execution = next(
                (
                    citation.execution
                    for citation in envelope.source_citations
                    if citation.execution is not None
                ),
                None,
            )
            row_id = str(uuid4())
            row = Feed402EnvelopeRow(
                id=row_id,
                campaign_run_id=campaign_run_id,
                retrieval_run_id=retrieval_run_id,
                operation=record.operation,
                spec=spec,
                merchant=merchant,
                received_at=record.received_at,
                request_id=first_execution.request_id if first_execution is not None else None,
                query_fingerprint=(
                    first_execution.query_fingerprint if first_execution is not None else None
                ),
                response_sha256=(
                    first_execution.response_sha256 if first_execution is not None else None
                ),
                citation_count=len(envelope.citation),
                lineage_count=len(envelope.lineage),
                envelope_json=envelope.raw,
            )
            self.session.add(row)
            ids.append(row_id)
            citation_count += row.citation_count
            lineage_count += row.lineage_count
        self.session.flush()
        return Feed402PersistenceSummary(
            envelope_ids=ids,
            envelope_count=len(ids),
            citation_count=citation_count,
            lineage_count=lineage_count,
            specs=[spec] if spec is not None and ids else [],
        )
