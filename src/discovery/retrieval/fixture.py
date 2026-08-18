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
    boundary_kind = "fixture"

    def __init__(
        self,
        hits: list[RetrievalHit] | None = None,
        *,
        references: dict[str, CitationResponse] | None = None,
        cited_by: dict[str, CitationResponse] | None = None,
        assets: dict[str, AssetResponse] | None = None,
    ) -> None:
        self._hits = hits or []
        self._references = references or {}
        self._cited_by = cited_by or {}
        self._assets = assets or {}

    def search(self, query: SearchQuery) -> SearchResponse:
        return SearchResponse(query=query, hits=self._hits[: query.limit])

    def fetch(self, identifier: str) -> FetchResponse:
        for hit in self._hits:
            if hit.work and any(item.value == identifier for item in hit.work.identifiers):
                return FetchResponse(provider=self.name, work=hit.work)
        return FetchResponse(provider=self.name, work=None)

    def references(self, identifier: str) -> CitationResponse:
        if identifier not in self._references:
            raise CapabilityUnavailable("fixture provider has no references fixture for identifier")
        return self._references[identifier]

    def cited_by(self, identifier: str) -> CitationResponse:
        if identifier not in self._cited_by:
            raise CapabilityUnavailable("fixture provider has no cited-by fixture for identifier")
        return self._cited_by[identifier]

    def assets(self, identifier: str) -> AssetResponse:
        if identifier not in self._assets:
            raise CapabilityUnavailable("fixture provider has no asset fixture for identifier")
        return self._assets[identifier]
