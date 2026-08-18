from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.multiview import MultiViewSimilarity
from discovery.analysis.relations import RelationHypothesis, classify_relation
from discovery.core.ids import stable_id


class CrossDomainDiscoveryCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    problem_a_id: str
    problem_b_id: str
    discipline_a: str
    discipline_b: str
    similarity: MultiViewSimilarity
    relation_hypothesis: RelationHypothesis
    candidate_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    rejection_reasons: list[str] = Field(default_factory=list)
    review_status: str = "unreviewed"


def rank_cross_domain_candidates(
    similarities: list[MultiViewSimilarity],
    disciplines: dict[str, str],
    *,
    minimum_score: float = 0.25,
) -> list[CrossDomainDiscoveryCandidate]:
    result: list[CrossDomainDiscoveryCandidate] = []
    for similarity in similarities:
        left_field = disciplines.get(similarity.problem_a_id, "unknown")
        right_field = disciplines.get(similarity.problem_b_id, "unknown")
        if left_field == right_field or "unknown" in {left_field, right_field}:
            continue
        novelty = similarity.independence_score
        score = 0.72 * similarity.aggregate_score + 0.28 * novelty
        if score < minimum_score:
            continue
        rejection: list[str] = []
        if similarity.evidence.lexical > 0.70:
            rejection.append("lexical overlap is high; cross-domain novelty may be superficial")
        if similarity.evidence.citation_connectivity > 0.55:
            rejection.append("literatures are strongly citation-connected")
        result.append(
            CrossDomainDiscoveryCandidate(
                id=stable_id(
                    "cross-domain-v010",
                    f"{similarity.problem_a_id}:{similarity.problem_b_id}",
                ),
                problem_a_id=similarity.problem_a_id,
                problem_b_id=similarity.problem_b_id,
                discipline_a=left_field,
                discipline_b=right_field,
                similarity=similarity,
                relation_hypothesis=classify_relation(similarity),
                candidate_score=round(max(0.0, min(1.0, score)), 6),
                novelty_score=novelty,
                rejection_reasons=rejection,
            )
        )
    return sorted(result, key=lambda item: (-item.candidate_score, item.id))
