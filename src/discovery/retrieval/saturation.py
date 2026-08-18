from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SaturationObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iteration: int = Field(ge=1)
    retrieved: int = Field(ge=0)
    new_unique_works: int = Field(ge=0)
    cumulative_unique_works: int = Field(ge=0)

    @property
    def novelty_rate(self) -> float:
        return 0.0 if self.retrieved == 0 else self.new_unique_works / self.retrieved


class SaturationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_iterations: int = Field(default=3, ge=1)
    window: int = Field(default=3, ge=1)
    novelty_threshold: float = Field(default=0.03, ge=0, le=1)

    def saturated(self, observations: list[SaturationObservation]) -> bool:
        if len(observations) < max(self.minimum_iterations, self.window):
            return False
        recent = observations[-self.window :]
        return all(item.novelty_rate <= self.novelty_threshold for item in recent)
