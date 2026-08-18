from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryYield(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iteration: int = Field(ge=1)
    retrieved: int = Field(ge=0)
    new_works: int = Field(ge=0)
    new_terms: int = Field(default=0, ge=0)
    new_concepts: int = Field(default=0, ge=0)
    new_citations: int = Field(default=0, ge=0)
    new_problem_signatures: int = Field(default=0, ge=0)

    def normalized_novelty(self) -> float:
        if self.retrieved == 0:
            return 0.0
        weighted = (
            self.new_works
            + 0.35 * self.new_terms
            + 0.75 * self.new_concepts
            + 0.20 * self.new_citations
            + 0.90 * self.new_problem_signatures
        )
        return min(1.0, weighted / self.retrieved)


class AuditedSaturationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_iterations: int = Field(default=4, ge=2)
    window: int = Field(default=3, ge=2)
    novelty_threshold: float = Field(default=0.04, ge=0, le=1)
    require_strata_stability: bool = True

    def saturated(self, yields: list[DiscoveryYield], strata_stable: bool) -> bool:
        if len(yields) < max(self.minimum_iterations, self.window):
            return False
        if self.require_strata_stability and not strata_stable:
            return False
        return all(
            item.normalized_novelty() <= self.novelty_threshold
            for item in yields[-self.window :]
        )
