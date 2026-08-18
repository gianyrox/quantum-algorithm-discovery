from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PipelineStage(StrEnum):
    RETRIEVAL = "retrieval"
    CORPUS = "corpus"
    DOCUMENTS = "documents"
    PROBLEMS = "problems"
    MATHEMATICS = "mathematics"
    ANALYSIS = "analysis"
    DISCOVERY = "discovery"
    QUANTUM = "quantum"
    EVALUATION = "evaluation"


class StageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: PipelineStage
    status: str
    input_ids: list[str] = Field(default_factory=list)
    output_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
