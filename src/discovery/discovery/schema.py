from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.similarity import SimilarityEvidence


class CrossDomainCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    problem_a_id: str
    problem_b_id: str
    field_a: str
    field_b: str
    similarity: SimilarityEvidence
    shared_structures: list[str] = Field(default_factory=list)
    important_differences: list[str] = Field(default_factory=list)
    known_cross_field_connection: bool | None = None
    historical_connection: bool | None = None
    possible_independent_rediscovery: bool | None = None
    candidate_score: float = Field(ge=0, le=1)
    review_status: str = "unreviewed"
    evidence: list[str] = Field(default_factory=list)
