from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BenchmarkSplit(StrEnum):
    PILOT = "pilot"
    DEVELOPMENT = "development"
    TEST = "test"


class SelectionStatus(StrEnum):
    CANDIDATE = "candidate"
    SELECTED = "selected"
    REJECTED = "rejected"
    ANNOTATING = "annotating"
    ANNOTATED = "annotated"


class BenchmarkWork(BaseModel):
    """
    A scientific work selected or considered for a benchmark.

    This records benchmark sampling and source identity separately from
    any interpretation of the computational problems in the work.
    """

    model_config = ConfigDict(extra="forbid")

    benchmark_work_id: str = Field(min_length=1)

    title: str
    discipline: str
    subdiscipline: str | None = None

    publication_year: int | None = Field(default=None, ge=1600, le=2100)

    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    openalex_id: str | None = None
    canonical_url: HttpUrl | None = None

    authors: list[str] = Field(default_factory=list)

    split: BenchmarkSplit = BenchmarkSplit.PILOT
    status: SelectionStatus = SelectionStatus.CANDIDATE

    selection_reason: str
    selection_method: str

    # These describe benchmark sampling, not the scientific problem itself.
    desired_diversity_axes: list[str] = Field(default_factory=list)

    source_available: bool = False
    full_text_available: bool | None = None

    rejection_reason: str | None = None
    notes: str | None = None


class BenchmarkCorpus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark_name: str
    version: str

    description: str

    works: list[BenchmarkWork] = Field(default_factory=list)
