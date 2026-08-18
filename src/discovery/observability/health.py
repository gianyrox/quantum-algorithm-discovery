from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from discovery.storage.models import ConceptRow, ProblemInstanceRow, RetrievalRunRow, WorkRow


class DoctorReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    database_healthy: bool
    works: int = Field(ge=0)
    problems: int = Field(ge=0)
    concepts: int = Field(ge=0)
    retrieval_runs: int = Field(ge=0)
    gateway_configured: bool = False
    gateway_healthy: bool | None = None
    gateway_error: str | None = None


def database_counts(session: Session) -> dict[str, int]:
    return {
        "works": int(session.scalar(select(func.count()).select_from(WorkRow)) or 0),
        "problems": int(
            session.scalar(select(func.count()).select_from(ProblemInstanceRow)) or 0
        ),
        "concepts": int(session.scalar(select(func.count()).select_from(ConceptRow)) or 0),
        "retrieval_runs": int(
            session.scalar(select(func.count()).select_from(RetrievalRunRow)) or 0
        ),
    }
