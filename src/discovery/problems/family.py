from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProblemFamily(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    problem_ids: list[str] = Field(default_factory=list)
    shared_task_families: list[str] = Field(default_factory=list)
    shared_mathematical_structures: list[str] = Field(default_factory=list)
    shared_operations: list[str] = Field(default_factory=list)
    distinguishing_features: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    status: str = "candidate"
