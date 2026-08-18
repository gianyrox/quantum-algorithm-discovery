from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from discovery.core.provenance import ProvenanceRecord
from discovery.corpus.schema import Asset, Work


class SearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    limit: int = Field(default=25, ge=1, le=1000)
    providers: list[str] = Field(default_factory=list)
    filters: dict[str, object] = Field(default_factory=dict)
    max_cost_usd: float | None = Field(default=None, ge=0)


class QueryClause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    source: str
    concept_id: str | None = None
    term_type: str | None = None
    weight: float = Field(default=1.0, gt=0)


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    clauses: list[QueryClause]
    rendered_query: str
    concept_ids: list[str] = Field(default_factory=list)
    discipline_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    provider_rank: int = Field(ge=1)
    provider_score: float | None = None
    fused_rank: int | None = Field(default=None, ge=1)
    work: Work | None = None
    raw_record: dict[str, object] = Field(default_factory=dict)
    provenance: ProvenanceRecord | None = None


class ProviderReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: str
    status: str
    result_count: int | None = None
    reason: str | None = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: SearchQuery
    hits: list[RetrievalHit]
    provider_reports: list[ProviderReport] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_envelope: dict[str, object] = Field(default_factory=dict)


class FetchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    work: Work | None
    provenance: ProvenanceRecord | None = None
    raw_envelope: dict[str, object] = Field(default_factory=dict)


class CitationEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    target_id: str
    provider: str
    provider_edge_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    provenance: ProvenanceRecord | None = None


class CitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str
    direction: str
    edges: list[CitationEdge]
    provider_reports: list[ProviderReport] = Field(default_factory=list)


class AssetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str
    assets: list[Asset]
    provider_reports: list[ProviderReport] = Field(default_factory=list)
