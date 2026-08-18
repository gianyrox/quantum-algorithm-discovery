from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class SoftwareIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    software: str
    software_version: str | None = None
    git_commit: str | None = None


class RightsStatement(BaseModel):
    """Rights as observed, never inferred from access alone."""

    model_config = ConfigDict(extra="forbid")

    metadata_license: str | None = None
    content_license: str | None = None
    redistribution: str = "unknown"
    tdm: str = "unknown"
    model_training: str = "unknown"
    retention: str = "unknown"
    terms_url: str | None = None
    retrieved_at: datetime | None = None


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    source_identifier: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provider_release: str | None = None
    request_id: str | None = None
    query_fingerprint: str | None = None
    provider_request_fingerprint: str | None = None
    response_sha256: str | None = None
    software: SoftwareIdentity | None = None
    raw_record_sha256: str | None = None


class DerivationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    derived_object_id: str
    source_object_ids: list[str]
    transformation: str
    software: SoftwareIdentity
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parameters: dict[str, object] = Field(default_factory=dict)
