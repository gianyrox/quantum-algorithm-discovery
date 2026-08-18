from __future__ import annotations

from discovery.retrieval.models import (
    AssetResponse,
    CitationResponse,
    FetchResponse,
    RetrievalHit,
    SearchQuery,
    SearchResponse,
)
from discovery.retrieval.provider import CapabilityUnavailable


class FixtureProvider:
    """Deterministic offline provider used for tests and early pilots."""

    name = "fixture"

    def __init__(self, hits: list[RetrievalHit] | None = None) -> None:
        self._hits = hits or []

    def search(self, query: SearchQuery) -> SearchResponse:
        return SearchResponse(query=query, hits=self._hits[: query.limit])

    def fetch(self, identifier: str) -> FetchResponse:
        for hit in self._hits:
            if hit.work and any(item.value == identifier for item in hit.work.identifiers):
                return FetchResponse(provider=self.name, work=hit.work)
        return FetchResponse(provider=self.name, work=None)

    def references(self, identifier: str) -> CitationResponse:
        raise CapabilityUnavailable("fixture provider has no citation fixture")

    def cited_by(self, identifier: str) -> CitationResponse:
        raise CapabilityUnavailable("fixture provider has no citation fixture")

    def assets(self, identifier: str) -> AssetResponse:
        raise CapabilityUnavailable("fixture provider has no asset fixture")
