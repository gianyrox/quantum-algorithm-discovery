from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.multiview import MultiViewSimilarity


class CrossDomainRelation(StrEnum):
    EQUIVALENT_FORMULATION = "equivalent_formulation"
    SHARED_MATHEMATICAL_FORM = "shared_mathematical_form"
    SHARED_MECHANISM = "shared_mechanism"
    SHARED_FUNCTION_DIFFERENT_MECHANISM = "shared_function_different_mechanism"
    HISTORICAL_TRANSMISSION = "historical_transmission"
    INDEPENDENT_REDISCOVERY = "independent_rediscovery"
    ANALOGY = "analogy"
    LEXICAL_RESEMBLANCE = "lexical_resemblance"
    UNRESOLVED = "unresolved"


class RelationHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_a_id: str
    problem_b_id: str
    relation: CrossDomainRelation
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    requires_review: bool = True


def classify_relation(similarity: MultiViewSimilarity) -> RelationHypothesis:
    evidence = similarity.evidence
    if evidence.lexical > 0.75 and similarity.structural_score < 0.25:
        relation = CrossDomainRelation.LEXICAL_RESEMBLANCE
        confidence = evidence.lexical
        reasons = ["high lexical overlap without corresponding structural overlap"]
    elif similarity.structural_score >= 0.60 and similarity.independence_score >= 0.55:
        relation = CrossDomainRelation.SHARED_MATHEMATICAL_FORM
        confidence = min(0.9, 0.55 + 0.35 * similarity.structural_score)
        reasons = ["strong structural resemblance", "weak lexical/citation connectivity"]
    elif similarity.aggregate_score >= 0.45:
        relation = CrossDomainRelation.ANALOGY
        confidence = similarity.aggregate_score
        reasons = ["moderate multi-view resemblance; equivalence is not established"]
    else:
        relation = CrossDomainRelation.UNRESOLVED
        confidence = 1.0 - similarity.aggregate_score
        reasons = ["insufficient evidence for a stronger cross-domain relation"]
    return RelationHypothesis(
        problem_a_id=similarity.problem_a_id,
        problem_b_id=similarity.problem_b_id,
        relation=relation,
        confidence=round(confidence, 6),
        reasons=reasons,
    )
