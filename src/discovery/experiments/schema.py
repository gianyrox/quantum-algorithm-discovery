from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class ExperimentArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    kind: str
    checksum: str | None = None


class ExperimentRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    experiment_type: str
    status: str = "running"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    config: dict[str, object] = Field(default_factory=dict)
    metrics: dict[str, object] = Field(default_factory=dict)
    artifacts: list[ExperimentArtifact] = Field(default_factory=list)
    notes: str | None = None
