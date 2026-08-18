from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrievalBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    maximum_requests: int = Field(default=100, ge=1)
    maximum_results: int = Field(default=10000, ge=1)
    maximum_cost_usd: float | None = Field(default=None, ge=0)
    requests_used: int = Field(default=0, ge=0)
    results_seen: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0)

    def exhausted(self) -> bool:
        if self.requests_used >= self.maximum_requests:
            return True
        if self.results_seen >= self.maximum_results:
            return True
        return self.maximum_cost_usd is not None and self.cost_usd >= self.maximum_cost_usd

    def record(self, *, requests: int = 1, results: int = 0, cost_usd: float = 0.0) -> None:
        self.requests_used += max(0, requests)
        self.results_seen += max(0, results)
        self.cost_usd += max(0.0, cost_usd)
