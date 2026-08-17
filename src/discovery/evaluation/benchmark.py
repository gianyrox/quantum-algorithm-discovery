from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class Annotator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str | None = None
    kind: str = "human"


class ProblemAnnotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark_id: str
    discipline: str
    subdiscipline: str | None = None

    work_id: str
    work_title: str
    publication_year: int | None = None

    problem: ProblemInstance

    annotator: Annotator

    annotation_guideline_version: str = "0.1"
    annotated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    notes: str | None = None
