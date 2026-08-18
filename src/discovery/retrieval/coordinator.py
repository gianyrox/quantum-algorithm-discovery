from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from discovery.retrieval.deep_harvest import DeepHarvestEngine, DeepHarvestPolicy, DeepHarvestResult
from discovery.retrieval.models import SearchQuery
from discovery.retrieval.paging import PagedResearchProvider
from discovery.retrieval.saturation import SaturationPolicy


class MultiProviderHarvestPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_pages_per_provider: int = Field(default=20, ge=1, le=100000)
    max_records_per_provider: int | None = Field(default=None, ge=1)
    saturation: SaturationPolicy | None = None
    continue_on_provider_error: bool = True


class MultiProviderHarvestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: SearchQuery
    provider_results: list[DeepHarvestResult] = Field(default_factory=list)
    unique_work_ids: list[str] = Field(default_factory=list)
    total_pages: int = Field(ge=0)
    total_hits: int = Field(ge=0)
    errors: list[str] = Field(default_factory=list)


class DirectHarvestCoordinator:
    """Run resumable deep retrieval across providers without sharing provider state.

    Execution is intentionally sequential at the SQLAlchemy-session boundary.
    Provider-native pagination and checkpoints stay independent, and failures in
    one source do not erase evidence from other sources.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(
        self,
        query: SearchQuery,
        providers: dict[str, PagedResearchProvider],
        *,
        policy: MultiProviderHarvestPolicy | None = None,
    ) -> MultiProviderHarvestResult:
        resolved = policy or MultiProviderHarvestPolicy()
        results: list[DeepHarvestResult] = []
        work_ids: set[str] = set()
        errors: list[str] = []
        total_pages = 0
        total_hits = 0
        for provider_name, provider in providers.items():
            provider_query = query.model_copy(update={"providers": [provider_name]})
            try:
                result = DeepHarvestEngine(self.session, provider).execute(
                    provider_query,
                    policy=DeepHarvestPolicy(
                        max_pages=resolved.max_pages_per_provider,
                        max_records=resolved.max_records_per_provider,
                        saturation=resolved.saturation,
                        stop_on_error=not resolved.continue_on_provider_error,
                    ),
                )
                results.append(result)
                work_ids.update(result.unique_work_ids)
                total_pages += result.pages
                total_hits += result.hits
                errors.extend(f"{provider_name}:{item}" for item in result.errors)
            except Exception as exc:
                message = f"{provider_name}:{type(exc).__name__}:{exc}"
                errors.append(message)
                if not resolved.continue_on_provider_error:
                    raise
        return MultiProviderHarvestResult(
            query=query,
            provider_results=results,
            unique_work_ids=sorted(work_ids),
            total_pages=total_pages,
            total_hits=total_hits,
            errors=errors,
        )
