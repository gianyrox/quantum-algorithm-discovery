from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class IdentityAssertion(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_identifier: str
    relation_type: str
    target_identifier: str
    provider: str
    confidence: float | None = None
    payload: dict[str, object] = Field(default_factory=dict)


class IdentityResolution(BaseModel):
    model_config = ConfigDict(extra="allow")

    query_identifier: str
    assertions: list[IdentityAssertion] = Field(default_factory=list)
    provider_reports: list[dict[str, object]] = Field(default_factory=list)
    raw_envelope: dict[str, object] = Field(default_factory=dict)


class IntegrityAssertion(BaseModel):
    model_config = ConfigDict(extra="allow")

    subject_identifier: str
    relation_type: str
    object_identifier: str | None = None
    provider: str
    notice_date: datetime | None = None
    status: str = "asserted"
    payload: dict[str, object] = Field(default_factory=dict)


class IntegrityReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    query_identifier: str
    assertions: list[IntegrityAssertion] = Field(default_factory=list)
    provider_reports: list[dict[str, object]] = Field(default_factory=list)
    raw_envelope: dict[str, object] = Field(default_factory=dict)


class GatewaySyncProvider(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: str
    status: str = "unknown"
    capabilities: list[str] = Field(default_factory=list)
    bulk: dict[str, object] = Field(default_factory=dict)
    incremental: dict[str, object] = Field(default_factory=dict)
    last_verified: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)


class GatewaySyncReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    providers: list[GatewaySyncProvider] = Field(default_factory=list)
    raw_envelope: dict[str, object] = Field(default_factory=dict)


class GatewayCoverageReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dimensions: dict[str, object] = Field(default_factory=dict)
    gaps: list[dict[str, object]] = Field(default_factory=list)
    raw_envelope: dict[str, object] = Field(default_factory=dict)


class GatewayHarvestPage(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: str | None = None
    records: list[dict[str, object]] = Field(default_factory=list)
    cursor: str | None = None
    exhausted: bool = False
    cursor_ephemeral: bool | None = None
    raw_envelope: dict[str, object] = Field(default_factory=dict)
