from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from discovery.coverage.active import RetrievalPriority
from discovery.coverage.saturation import AuditedSaturationPolicy, DiscoveryYield


class FeedbackAction(StrEnum):
    CONTINUE = "continue"
    EXPAND_TERMS = "expand_terms"
    EXPAND_CITATIONS = "expand_citations"
    ADD_PROVIDER = "add_provider"
    TARGET_HISTORY = "target_history"
    REVIEW_GAP = "review_gap"
    SATURATED = "saturated"


class FeedbackDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: FeedbackAction
    reason: str
    priority_scope_id: str | None = None
    suggested_terms: list[str] = Field(default_factory=list)


class FeedbackLoop:
    def __init__(self, saturation_policy: AuditedSaturationPolicy | None = None) -> None:
        self.saturation_policy = saturation_policy or AuditedSaturationPolicy()

    def decide(
        self,
        yields: list[DiscoveryYield],
        priorities: list[RetrievalPriority],
        *,
        strata_stable: bool,
        unknown_terms: list[str] | None = None,
    ) -> FeedbackDecision:
        if self.saturation_policy.saturated(yields, strata_stable):
            return FeedbackDecision(
                action=FeedbackAction.SATURATED, reason="audited saturation met"
            )
        unknown_terms = unknown_terms or []
        if unknown_terms:
            return FeedbackDecision(
                action=FeedbackAction.EXPAND_TERMS,
                reason="candidate corpus language is absent from known retrieval vocabulary",
                suggested_terms=unknown_terms[:20],
            )
        if priorities:
            top = priorities[0]
            if top.historical_gap >= 0.6:
                action = FeedbackAction.TARGET_HISTORY
            elif top.coverage_gap >= 0.6 and top.provider_disagreement >= 0.3:
                action = FeedbackAction.ADD_PROVIDER
            else:
                action = FeedbackAction.CONTINUE
            return FeedbackDecision(
                action=action,
                reason="highest expected information gain scope",
                priority_scope_id=top.scope_id,
            )
        return FeedbackDecision(
            action=FeedbackAction.REVIEW_GAP,
            reason="not saturated but no automatic retrieval priority is available",
        )
