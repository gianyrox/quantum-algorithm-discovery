from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_type: str
    object_id: str
    provider: str
    model: str
    model_version: str = "unknown"
    vector: list[float]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def dimensions(self) -> int:
        return len(self.vector)


class EmbeddingProvider(Protocol):
    name: str
    model: str
    model_version: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...
