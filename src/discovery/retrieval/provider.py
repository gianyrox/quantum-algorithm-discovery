from __future__ import annotations

from typing import Protocol

from discovery.retrieval.models import (
    AssetResponse,
    CitationResponse,
    FetchResponse,
    SearchQuery,
    SearchResponse,
)


class CapabilityUnavailable(RuntimeError):
    pass


class ResearchProvider(Protocol):
    name: str

    def search(self, query: SearchQuery) -> SearchResponse: ...

    def fetch(self, identifier: str) -> FetchResponse: ...

    def references(self, identifier: str) -> CitationResponse: ...

    def cited_by(self, identifier: str) -> CitationResponse: ...

    def assets(self, identifier: str) -> AssetResponse: ...
