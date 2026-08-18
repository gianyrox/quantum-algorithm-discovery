from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.features import hybrid_similarity
from discovery.analysis.similarity import SimilarityEvidence
from discovery.problems.schema import ProblemInstance


class SimilarityWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: float = 0.14
    mathematical: float = 0.20
    operator: float = 0.15
    constraint: float = 0.10
    topology: float = 0.08
    stochastic: float = 0.07
    complexity: float = 0.08
    method: float = 0.06
    semantic: float = 0.07
    lexical_penalty: float = 0.03
    citation_penalty: float = 0.02


class MultiViewSimilarity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_a_id: str
    problem_b_id: str
    evidence: SimilarityEvidence
    aggregate_score: float = Field(ge=0, le=1)
    structural_score: float = Field(ge=0, le=1)
    independence_score: float = Field(ge=0, le=1)
    explanation: list[str] = Field(default_factory=list)


def compare_problems(
    left: ProblemInstance,
    right: ProblemInstance,
    *,
    left_embedding: list[float] | None = None,
    right_embedding: list[float] | None = None,
    citation_connectivity: float = 0.0,
    weights: SimilarityWeights | None = None,
) -> MultiViewSimilarity:
    weights = weights or SimilarityWeights()
    evidence = hybrid_similarity(
        left,
        right,
        left_embedding=left_embedding,
        right_embedding=right_embedding,
        citation_connectivity=citation_connectivity,
    )
    positive = (
        weights.task * evidence.task
        + weights.mathematical * evidence.mathematical
        + weights.operator * evidence.operator
        + weights.constraint * evidence.constraint
        + weights.topology * evidence.topology
        + weights.stochastic * evidence.stochastic
        + weights.complexity * evidence.complexity
        + weights.method * evidence.method
        + weights.semantic * evidence.semantic
    )
    aggregate = positive - weights.lexical_penalty * evidence.lexical
    aggregate -= weights.citation_penalty * evidence.citation_connectivity
    aggregate = max(0.0, min(1.0, aggregate))
    independence = max(0.0, 1.0 - 0.55 * evidence.lexical - 0.45 * evidence.citation_connectivity)
    explanation = [
        f"task={evidence.task:.3f}",
        f"math={evidence.mathematical:.3f}",
        f"operator={evidence.operator:.3f}",
        f"lexical={evidence.lexical:.3f}",
        f"citation={evidence.citation_connectivity:.3f}",
    ]
    return MultiViewSimilarity(
        problem_a_id=left.id,
        problem_b_id=right.id,
        evidence=evidence,
        aggregate_score=round(aggregate, 6),
        structural_score=evidence.structural_score(),
        independence_score=round(independence, 6),
        explanation=explanation,
    )
