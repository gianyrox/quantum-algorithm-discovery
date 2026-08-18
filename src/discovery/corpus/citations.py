from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.corpus.resolution import parse_identifier
from discovery.retrieval.models import CitationEdge
from discovery.storage.models import ResearchObjectRelationRow, WorkIdentifierRow
from discovery.storage.repositories import CitationRepository


class CitationIngestReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_edges: int = Field(ge=0)
    canonical_edges: int = Field(ge=0)
    unresolved_edges: int = Field(ge=0)


class CitationIngestionService:
    """Preserve provider citation assertions without inventing canonical work IDs."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.citations = CitationRepository(session)

    def ingest(self, edges: list[CitationEdge]) -> CitationIngestReport:
        canonical = 0
        unresolved = 0
        for edge in edges:
            source_work = self._resolve(edge.source_id)
            target_work = self._resolve(edge.target_id)
            if source_work is not None and target_work is not None:
                self.citations.upsert_edge(
                    source_work_id=source_work,
                    target_work_id=target_work,
                    provider=edge.provider,
                    provider_edge_id=edge.provider_edge_id,
                    metadata=edge.metadata,
                )
                canonical += 1
            else:
                self._store_external(edge)
                unresolved += 1
        return CitationIngestReport(
            observed_edges=len(edges),
            canonical_edges=canonical,
            unresolved_edges=unresolved,
        )

    def materialize_canonical_edges(self) -> int:
        rows = list(
            self.session.scalars(
                select(ResearchObjectRelationRow).where(
                    ResearchObjectRelationRow.subject_type == "external_identifier",
                    ResearchObjectRelationRow.relation_type == "cites",
                    ResearchObjectRelationRow.object_type == "external_identifier",
                )
            )
        )
        created = 0
        for row in rows:
            source_work = self._resolve(row.subject_id)
            target_work = self._resolve(row.object_id)
            if source_work is None or target_work is None:
                continue
            self.citations.upsert_edge(
                source_work_id=source_work,
                target_work_id=target_work,
                provider=row.provider,
                metadata=row.payload_json,
            )
            created += 1
        return created

    def _resolve(self, value: str) -> str | None:
        parsed = parse_identifier(value)
        if parsed is None:
            return None
        scheme, normalized = parsed
        row = self.session.scalar(
            select(WorkIdentifierRow).where(
                WorkIdentifierRow.scheme == scheme,
                WorkIdentifierRow.value == normalized,
            )
        )
        return row.work_id if row is not None else None

    def _store_external(self, edge: CitationEdge) -> None:
        existing = self.session.scalar(
            select(ResearchObjectRelationRow).where(
                ResearchObjectRelationRow.subject_type == "external_identifier",
                ResearchObjectRelationRow.subject_id == edge.source_id,
                ResearchObjectRelationRow.relation_type == "cites",
                ResearchObjectRelationRow.object_type == "external_identifier",
                ResearchObjectRelationRow.object_id == edge.target_id,
                ResearchObjectRelationRow.provider == edge.provider,
            )
        )
        if existing is None:
            existing = ResearchObjectRelationRow(
                subject_type="external_identifier",
                subject_id=edge.source_id,
                relation_type="cites",
                native_relation_type="citation",
                object_type="external_identifier",
                object_id=edge.target_id,
                provider=edge.provider,
                retrieved_at=datetime.now(UTC),
                payload_json=edge.metadata,
            )
        else:
            existing.retrieved_at = datetime.now(UTC)
            existing.payload_json = edge.metadata
        self.session.add(existing)
        self.session.flush()
