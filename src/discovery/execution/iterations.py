from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from discovery.coverage.feedback import FeedbackDecision
from discovery.coverage.saturation import DiscoveryYield


class IterationStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    SATURATED = "saturated"
    FAILED = "failed"


class DiscoveryIteration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    campaign_id: str
    iteration: int = Field(ge=1)
    status: IterationStatus = IterationStatus.PLANNED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    discovery_yield: DiscoveryYield | None = None
    feedback: FeedbackDecision | None = None
    query_plan_ids: list[str] = Field(default_factory=list)
    retrieval_run_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def start(self) -> None:
        self.status = IterationStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def finish(self, discovery_yield: DiscoveryYield, feedback: FeedbackDecision) -> None:
        self.discovery_yield = discovery_yield
        self.feedback = feedback
        self.completed_at = datetime.now(UTC)
        self.status = (
            IterationStatus.SATURATED
            if feedback.action.value == "saturated"
            else IterationStatus.COMPLETED
        )
