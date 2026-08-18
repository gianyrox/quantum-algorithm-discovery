from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import DeclarativeBase, Session

from discovery.core.ids import stable_id
from discovery.storage.models import (
    AssetRow,
    CitationRow,
    ConceptRow,
    CoverageSnapshotRow,
    DisciplineRow,
    DocumentRow,
    IdentityAssertionRow,
    IntegrityAssertionRow,
    ProblemInstanceRow,
    ProcessingJobRow,
    ProviderRequestRow,
    RetrievalHitRow,
    RetrievalRunRow,
    TermRow,
    WorkRow,
)


class CoverageSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    scope: str
    created_at: datetime
    metrics: dict[str, int | float | str]
    task_families: dict[str, int] = Field(default_factory=dict)
    retrieval_providers: dict[str, int] = Field(default_factory=dict)
    publication_years: dict[str, int] = Field(default_factory=dict)
    gaps: list[dict[str, object]] = Field(default_factory=list)


def _count(session: Session, model: type[DeclarativeBase]) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


class CoverageService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def snapshot(self, *, scope: str = "default") -> CoverageSnapshot:
        task_families = {
            name: int(count)
            for name, count in self.session.execute(
                select(ProblemInstanceRow.task_family, func.count()).group_by(
                    ProblemInstanceRow.task_family
                )
            )
        }
        providers = {
            name: int(count)
            for name, count in self.session.execute(
                select(RetrievalHitRow.provider, func.count()).group_by(RetrievalHitRow.provider)
            )
        }
        years = {
            str(year): int(count)
            for year, count in self.session.execute(
                select(WorkRow.publication_year, func.count())
                .where(WorkRow.publication_year.is_not(None))
                .group_by(WorkRow.publication_year)
            )
        }
        metrics: dict[str, int | float | str] = {
            "works": _count(self.session, WorkRow),
            "problems": _count(self.session, ProblemInstanceRow),
            "retrieval_runs": _count(self.session, RetrievalRunRow),
            "provider_requests": _count(self.session, ProviderRequestRow),
            "assets": _count(self.session, AssetRow),
            "documents": _count(self.session, DocumentRow),
            "citations": _count(self.session, CitationRow),
            "identity_assertions": _count(self.session, IdentityAssertionRow),
            "integrity_assertions": _count(self.session, IntegrityAssertionRow),
            "processing_jobs": _count(self.session, ProcessingJobRow),
            "disciplines": _count(self.session, DisciplineRow),
            "concepts": _count(self.session, ConceptRow),
            "terms": _count(self.session, TermRow),
        }
        gaps: list[dict[str, object]] = []
        if metrics["works"] == 0:
            gaps.append({"dimension": "corpus", "state": "empty", "note": "No works ingested."})
        if metrics["problems"] == 0:
            gaps.append(
                {
                    "dimension": "problem_representation",
                    "state": "empty",
                    "note": "No ProblemInstance records.",
                }
            )
        created = datetime.now(UTC)
        snapshot = CoverageSnapshot(
            id=stable_id("coverage-snapshot", f"{scope}:{created.isoformat()}"),
            scope=scope,
            created_at=created,
            metrics=metrics,
            task_families=task_families,
            retrieval_providers=providers,
            publication_years=years,
            gaps=gaps,
        )
        self.session.add(
            CoverageSnapshotRow(
                id=snapshot.id,
                scope=scope,
                created_at=created,
                metrics_json={
                    "metrics": metrics,
                    "task_families": task_families,
                    "retrieval_providers": providers,
                    "publication_years": years,
                },
                gaps_json=gaps,
            )
        )
        self.session.flush()
        return snapshot
