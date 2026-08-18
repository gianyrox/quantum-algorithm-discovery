from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class SoftwareComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    config_fingerprint: str | None = None


class ResearchManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    corpus_release: str | None = None
    ontology_releases: dict[str, str] = Field(default_factory=dict)
    query_plan_version: str | None = None
    extractor: SoftwareComponent | None = None
    math_normalizer: SoftwareComponent | None = None
    embedding: SoftwareComponent | None = None
    similarity: SoftwareComponent | None = None
    clustering: SoftwareComponent | None = None
    source_code_revision: str | None = None
    notes: list[str] = Field(default_factory=list)

    def fingerprint(self) -> str:
        payload = self.model_dump_json(exclude={"id", "created_at"})
        return hashlib.sha256(payload.encode()).hexdigest()
