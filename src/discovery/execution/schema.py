from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from discovery.retrieval.harvest import HarvestPolicy


class CampaignScope(StrEnum):
    CONCEPT = "concept"
    DISCIPLINE = "discipline"
    QUERY = "query"


class ProcessingStage(StrEnum):
    IDENTITY_RESOLUTION = "identity_resolution"
    INTEGRITY_CHECK = "integrity_check"
    ASSET_DISCOVERY = "asset_discovery"
    ASSET_ACQUISITION = "asset_acquisition"
    DOCUMENT_PARSE = "document_parse"
    PROBLEM_EXTRACTION = "problem_extraction"
    MATHEMATICS = "mathematics"
    STRUCTURAL_ANALYSIS = "structural_analysis"


class CampaignConfig(BaseModel):
    """Immutable execution intent for one scientific retrieval campaign."""

    model_config = ConfigDict(extra="forbid")

    scope_type: CampaignScope
    scope_id: str
    name: str | None = None
    terms_per_query: int = Field(default=8, ge=1, le=100)
    result_limit: int = Field(default=50, ge=1, le=1000)
    max_concepts: int = Field(default=100, ge=1, le=5000)
    providers: list[str] = Field(default_factory=list)
    max_cost_usd: float | None = Field(default=None, ge=0)
    harvest_policy: HarvestPolicy = Field(default_factory=HarvestPolicy)
    enrich_identity: bool = False
    enrich_integrity: bool = False
    enqueue_asset_processing: bool = False
    enrichment_limit: int = Field(default=100, ge=0, le=10000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CampaignRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaign_id: str
    run_id: str
    status: str
    started_at: datetime
    completed_at: datetime
    query_plan_id: str | None = None
    query_batch_id: str | None = None
    unique_work_ids: list[str] = Field(default_factory=list)
    retrieval_hits: int = Field(default=0, ge=0)
    identity_assertions: int = Field(default=0, ge=0)
    integrity_assertions: int = Field(default=0, ge=0)
    jobs_enqueued: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)


class ProcessingJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    work_id: str
    asset_id: str | None = None
    stage: ProcessingStage
    status: str
    priority: int = 0
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    available_at: datetime
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)


class QueueStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pending: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    by_stage: dict[str, int] = Field(default_factory=dict)


class CorpusExportSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    works: int = Field(ge=0)
    identifiers: int = Field(ge=0)
    assets: int = Field(ge=0)
    citations: int = Field(ge=0)
    problems: int = Field(ge=0)
    output_path: str
