from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import DeclarativeBase, Session

from discovery.storage.models import (
    AssetAcquisitionRow,
    AssetRow,
    CitationRow,
    DocumentRow,
    IdentityAssertionRow,
    IntegrityAssertionRow,
    ProcessingJobRow,
    ProviderRequestRow,
    ResearchObjectRelationRow,
)


class OperationalSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_requests: int = Field(ge=0)
    provider_request_failures: int = Field(ge=0)
    assets: int = Field(ge=0)
    documents: int = Field(ge=0)
    canonical_citations: int = Field(ge=0)
    unresolved_citation_assertions: int = Field(ge=0)
    identity_assertions: int = Field(ge=0)
    integrity_assertions: int = Field(ge=0)
    asset_acquisitions: int = Field(ge=0)
    pending_jobs: int = Field(ge=0)
    failed_jobs: int = Field(ge=0)


def _count(session: Session, model: type[DeclarativeBase]) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


class OperationalObservabilityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def snapshot(self) -> OperationalSnapshot:
        request_failures = int(
            self.session.scalar(
                select(func.count())
                .select_from(ProviderRequestRow)
                .where(ProviderRequestRow.error.is_not(None))
            )
            or 0
        )
        unresolved_citations = int(
            self.session.scalar(
                select(func.count())
                .select_from(ResearchObjectRelationRow)
                .where(
                    ResearchObjectRelationRow.relation_type == "cites",
                    ResearchObjectRelationRow.subject_type == "external_identifier",
                )
            )
            or 0
        )
        pending_jobs = int(
            self.session.scalar(
                select(func.count())
                .select_from(ProcessingJobRow)
                .where(ProcessingJobRow.status == "pending")
            )
            or 0
        )
        failed_jobs = int(
            self.session.scalar(
                select(func.count())
                .select_from(ProcessingJobRow)
                .where(ProcessingJobRow.status == "failed")
            )
            or 0
        )
        return OperationalSnapshot(
            provider_requests=_count(self.session, ProviderRequestRow),
            provider_request_failures=request_failures,
            assets=_count(self.session, AssetRow),
            documents=_count(self.session, DocumentRow),
            canonical_citations=_count(self.session, CitationRow),
            unresolved_citation_assertions=unresolved_citations,
            identity_assertions=_count(self.session, IdentityAssertionRow),
            integrity_assertions=_count(self.session, IntegrityAssertionRow),
            asset_acquisitions=_count(self.session, AssetAcquisitionRow),
            pending_jobs=pending_jobs,
            failed_jobs=failed_jobs,
        )
