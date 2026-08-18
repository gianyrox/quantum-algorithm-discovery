from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import httpx

from discovery.retrieval.models import (
    AssetResponse,
    CitationResponse,
    FetchResponse,
    RetrievalHit,
    SearchQuery,
    SearchResponse,
)
from discovery.retrieval.provider import CapabilityUnavailable


class GenericJsonSearchProvider:
    """Configurable direct-provider fallback for simple JSON search APIs.

    It intentionally implements search only. Provider-specific identity, citation,
    asset, rights, and pagination semantics should live in the gateway or a more
    specific adapter rather than being guessed here.
    """

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        search_path: str,
        query_parameter: str,
        result_extractor: Callable[[Mapping[str, Any]], list[Mapping[str, Any]]],
        hit_normalizer: Callable[[Mapping[str, Any], int], RetrievalHit],
        client: httpx.Client | None = None,
    ) -> None:
        self.name = name
        self.search_path = search_path
        self.query_parameter = query_parameter
        self.result_extractor = result_extractor
        self.hit_normalizer = hit_normalizer
        self.client = client or httpx.Client(base_url=base_url, timeout=30.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def search(self, query: SearchQuery) -> SearchResponse:
        response = self.client.get(
            self.search_path,
            params={self.query_parameter: query.text, "limit": str(query.limit)},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError("direct provider returned non-object JSON")
        records = self.result_extractor(payload)
        hits = [self.hit_normalizer(record, rank) for rank, record in enumerate(records, start=1)]
        return SearchResponse(query=query, hits=hits[: query.limit], raw_envelope=dict(payload))

    def fetch(self, identifier: str) -> FetchResponse:
        raise CapabilityUnavailable("generic JSON fallback does not infer fetch semantics")

    def references(self, identifier: str) -> CitationResponse:
        raise CapabilityUnavailable("generic JSON fallback does not infer citation semantics")

    def cited_by(self, identifier: str) -> CitationResponse:
        raise CapabilityUnavailable("generic JSON fallback does not infer citation semantics")

    def assets(self, identifier: str) -> AssetResponse:
        raise CapabilityUnavailable("generic JSON fallback does not infer asset rights")
