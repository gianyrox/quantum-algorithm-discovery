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
    annotated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None


class ProblemAnnotationBundle(BaseModel):
    """Editable per-work annotation unit that may contain zero or many problems."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str
    benchmark_work_id: str
    discipline: str
    subdiscipline: str | None = None
    work_id: str
    work_title: str
    publication_year: int | None = None
    annotator: Annotator
    annotation_guideline_version: str = "0.1"
    problems: list[ProblemInstance] = Field(default_factory=list)
    notes: str | None = None

    def annotations(self) -> list[ProblemAnnotation]:
        return [
            ProblemAnnotation(
                benchmark_id=self.benchmark_id,
                discipline=self.discipline,
                subdiscipline=self.subdiscipline,
                work_id=self.work_id,
                work_title=self.work_title,
                publication_year=self.publication_year,
                problem=problem,
                annotator=self.annotator,
                annotation_guideline_version=self.annotation_guideline_version,
                notes=self.notes,
            )
            for problem in self.problems
        ]
