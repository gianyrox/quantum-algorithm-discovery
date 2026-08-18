from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from discovery.corpus.schema import Asset
from discovery.retrieval.models import (
    AssetResponse,
    CitationEdge,
    CitationResponse,
    FetchResponse,
    ProviderReport,
    RetrievalHit,
    SearchQuery,
    SearchResponse,
)
from discovery.retrieval.provider import CapabilityUnavailable, ResearchProvider


class FederatedDirectProvider:
    """Client-side federation for direct public providers.

    Provider records stay separate. Reciprocal-rank fusion only assigns a
    presentation rank; it never merges records or promotes fuzzy identity.
    """

    name = "direct-federation"

    def __init__(
        self,
        providers: list[ResearchProvider],
        *,
        max_workers: int = 4,
        rrf_k: int = 60,
    ) -> None:
        self.providers = providers
        self.max_workers = max_workers
        self.rrf_k = rrf_k

    def _selected(self, query: SearchQuery) -> list[ResearchProvider]:
        if not query.providers:
            return self.providers
        allowed = set(query.providers)
        return [provider for provider in self.providers if provider.name in allowed]

    def search(self, query: SearchQuery) -> SearchResponse:
        selected = self._selected(query)
        hits: list[RetrievalHit] = []
        reports: list[ProviderReport] = []
        worker_count = max(1, min(self.max_workers, len(selected) or 1))
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = {pool.submit(provider.search, query): provider for provider in selected}
            for future in as_completed(futures):
                provider = futures[future]
                try:
                    response = future.result()
                    hits.extend(response.hits)
                    reports.extend(response.provider_reports)
                    if not response.provider_reports:
                        reports.append(
                            ProviderReport(
                                provider=provider.name,
                                status="ok",
                                result_count=len(response.hits),
                            )
                        )
                except Exception as exc:
                    reports.append(
                        ProviderReport(
                            provider=provider.name,
                            status="error",
                            reason=f"{type(exc).__name__}:{exc}",
                        )
                    )
        scored: list[tuple[float, RetrievalHit]] = []
        for hit in hits:
            score = 1.0 / (self.rrf_k + hit.provider_rank)
            scored.append((score, hit))
        scored.sort(key=lambda item: (-item[0], item[1].provider, item[1].provider_rank))
        ranked: list[RetrievalHit] = []
        for fused_rank, (_score, hit) in enumerate(scored, start=1):
            ranked.append(hit.model_copy(update={"fused_rank": fused_rank}))
        return SearchResponse(query=query, hits=ranked[: query.limit], provider_reports=reports)

    def fetch(self, identifier: str) -> FetchResponse:
        errors: list[str] = []
        for provider in self.providers:
            try:
                response = provider.fetch(identifier)
                if response.work is not None:
                    return response
            except (CapabilityUnavailable, ValueError) as exc:
                errors.append(f"{provider.name}:{exc}")
        raise CapabilityUnavailable(
            f"no direct provider resolved {identifier!r}; " + "; ".join(errors)
        )

    def references(self, identifier: str) -> CitationResponse:
        edges: list[CitationEdge] = []
        reports: list[ProviderReport] = []
        for provider in self.providers:
            try:
                response = provider.references(identifier)
                edges.extend(response.edges)
                reports.extend(response.provider_reports)
            except CapabilityUnavailable as exc:
                reports.append(
                    ProviderReport(provider=provider.name, status="unsupported", reason=str(exc))
                )
        return CitationResponse(
            identifier=identifier,
            direction="references",
            edges=edges,
            provider_reports=reports,
        )

    def cited_by(self, identifier: str) -> CitationResponse:
        edges: list[CitationEdge] = []
        reports: list[ProviderReport] = []
        for provider in self.providers:
            try:
                response = provider.cited_by(identifier)
                edges.extend(response.edges)
                reports.extend(response.provider_reports)
            except CapabilityUnavailable as exc:
                reports.append(
                    ProviderReport(provider=provider.name, status="unsupported", reason=str(exc))
                )
        return CitationResponse(
            identifier=identifier,
            direction="cited_by",
            edges=edges,
            provider_reports=reports,
        )

    def assets(self, identifier: str) -> AssetResponse:
        assets: list[Asset] = []
        reports: list[ProviderReport] = []
        for provider in self.providers:
            try:
                response = provider.assets(identifier)
                assets.extend(response.assets)
                reports.extend(response.provider_reports)
            except CapabilityUnavailable as exc:
                reports.append(
                    ProviderReport(provider=provider.name, status="unsupported", reason=str(exc))
                )
        return AssetResponse(identifier=identifier, assets=assets, provider_reports=reports)
