from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.mathematics.structural import MathematicalFingerprint


class MathematicalSimilarity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exact: float = Field(ge=0, le=1)
    alpha_equivalent: float = Field(ge=0, le=1)
    token_overlap: float = Field(ge=0, le=1)
    operator_overlap: float = Field(ge=0, le=1)
    relation_match: float = Field(ge=0, le=1)
    structural_score: float = Field(ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


def _weighted_jaccard(left: dict[str, int], right: dict[str, int]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 0.0
    numerator = sum(min(left.get(key, 0), right.get(key, 0)) for key in keys)
    denominator = sum(max(left.get(key, 0), right.get(key, 0)) for key in keys)
    return numerator / denominator if denominator else 0.0


def _set_jaccard(left: list[str], right: list[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compare_fingerprints(
    left: MathematicalFingerprint, right: MathematicalFingerprint
) -> MathematicalSimilarity:
    exact = 1.0 if left.exact_sha256 == right.exact_sha256 else 0.0
    alpha = float(
        left.alpha_sha256 is not None
        and right.alpha_sha256 is not None
        and left.alpha_sha256 == right.alpha_sha256
    )
    token = _weighted_jaccard(left.token_multiset, right.token_multiset)
    operator = _set_jaccard(left.operator_signature, right.operator_signature)
    relation = float(left.relation_type is not None and left.relation_type == right.relation_type)
    score = 0.15 * exact + 0.30 * alpha + 0.25 * token + 0.20 * operator + 0.10 * relation
    return MathematicalSimilarity(
        exact=exact,
        alpha_equivalent=alpha,
        token_overlap=round(token, 6),
        operator_overlap=round(operator, 6),
        relation_match=relation,
        structural_score=round(score, 6),
        notes=["Multi-view mathematical resemblance; not a proof of mathematical equivalence."],
    )
