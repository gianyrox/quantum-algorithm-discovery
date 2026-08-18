from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrievalPriority(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope_id: str
    uncertainty: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    coverage_gap: float = Field(ge=0, le=1)
    historical_gap: float = Field(default=0.0, ge=0, le=1)
    provider_disagreement: float = Field(default=0.0, ge=0, le=1)
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)


def _as_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


class ActiveRetrievalPlanner:
    def prioritize(self, scopes: list[dict[str, object]]) -> list[RetrievalPriority]:
        priorities: list[RetrievalPriority] = []
        for item in scopes:
            scope_id = str(item["scope_id"])
            uncertainty = _as_float(item.get("uncertainty", 0.0))
            novelty = _as_float(item.get("novelty", 0.0))
            gap = _as_float(item.get("coverage_gap", 0.0))
            historical = _as_float(item.get("historical_gap", 0.0))
            disagreement = _as_float(item.get("provider_disagreement", 0.0))
            score = 0.30 * uncertainty + 0.25 * novelty + 0.30 * gap
            score += 0.10 * historical + 0.05 * disagreement
            reasons = []
            if gap >= 0.5:
                reasons.append("large coverage gap")
            if uncertainty >= 0.5:
                reasons.append("high uncertainty")
            if novelty >= 0.5:
                reasons.append("high recent novelty")
            if historical >= 0.5:
                reasons.append("historical terminology/decade gap")
            priorities.append(
                RetrievalPriority(
                    scope_id=scope_id,
                    uncertainty=uncertainty,
                    novelty=novelty,
                    coverage_gap=gap,
                    historical_gap=historical,
                    provider_disagreement=disagreement,
                    score=round(max(0.0, min(1.0, score)), 6),
                    reasons=reasons,
                )
            )
        return sorted(priorities, key=lambda item: (-item.score, item.scope_id))
