from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from discovery.core.ids import stable_id
from discovery.corpus.schema import IdentifierScheme, Work, WorkIdentifier, WorkVersion
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
from discovery.retrieval.provider import CapabilityUnavailable


class GatewayProtocolError(RuntimeError):
    pass


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_string(record: Mapping[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = record.get(name)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _normalize_identifier(record: Mapping[str, Any], provider: str) -> WorkIdentifier | None:
    candidates: tuple[tuple[str, IdentifierScheme], ...] = (
        ("doi", IdentifierScheme.DOI),
        ("pmid", IdentifierScheme.PMID),
        ("pmcid", IdentifierScheme.PMCID),
        ("arxiv_id", IdentifierScheme.ARXIV),
        ("openalex_id", IdentifierScheme.OPENALEX),
        ("id", IdentifierScheme.OTHER),
    )
    for key, scheme in candidates:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return WorkIdentifier(scheme=scheme, value=value, provider=provider, raw_value=value)
    return None


def _work_from_record(record: Mapping[str, Any], provider: str) -> Work | None:
    title = _first_string(record, ("title", "display_name", "name"))
    if title is None:
        return None
    identifier = _normalize_identifier(record, provider)
    raw_id = identifier.value if identifier else title
    year_value = record.get("publication_year", record.get("year"))
    year = year_value if isinstance(year_value, int) else None
    abstract = _first_string(record, ("abstract", "abstract_text", "summary"))
    return Work(
        id=stable_id("gateway-work", f"{provider}:{raw_id}"),
        title=title,
        abstract=abstract,
        publication_year=year,
        identifiers=[identifier] if identifier else [],
        version=WorkVersion(provider=provider, raw_record=dict(record)),
        metadata={"gateway_provider": provider},
    )


class GatewayProvider:
    """Client boundary for x402-research-gateway.

    The gateway is intentionally treated as an external capability service.
    Request/response parsing is permissive around additive feed402 fields but
    scientific-discovery never copies gateway provider logic into this repo.
    """

    name = "x402-research-gateway"

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(base_url=self.base_url, timeout=timeout_seconds)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def search(self, query: SearchQuery) -> SearchResponse:
        payload: dict[str, object] = {
            "query": query.text,
            "limit": query.limit,
        }
        if query.providers:
            payload["providers"] = query.providers
        if query.filters:
            payload["filters"] = query.filters
        if query.max_cost_usd is not None:
            payload["max_cost_usd"] = query.max_cost_usd

        response = self.client.post("/research/federated", json=payload)
        response.raise_for_status()
        envelope = response.json()
        if not isinstance(envelope, dict):
            raise GatewayProtocolError("gateway returned a non-object envelope")
        return self.parse_search_response(query, envelope)

    @staticmethod
    def parse_search_response(query: SearchQuery, envelope: Mapping[str, Any]) -> SearchResponse:
        data = _as_mapping(envelope.get("data"))
        results_obj = data.get("results", data.get("rows", data.get("hits", [])))
        results = results_obj if isinstance(results_obj, list) else []
        hits: list[RetrievalHit] = []
        for index, raw in enumerate(results, start=1):
            record = _as_mapping(raw)
            provider = _first_string(record, ("provider", "source", "source_id")) or "unknown"
            raw_record = _as_mapping(record.get("raw_record", record.get("record", record)))
            rank_value = record.get("provider_rank", record.get("rank", index))
            rank = rank_value if isinstance(rank_value, int) and rank_value > 0 else index
            fused_value = record.get("fused_rank")
            fused_rank = fused_value if isinstance(fused_value, int) and fused_value > 0 else None
            score_value = record.get("provider_score", record.get("score"))
            score = float(score_value) if isinstance(score_value, int | float) else None
            work = _work_from_record(raw_record, provider)
            hits.append(
                RetrievalHit(
                    provider=provider,
                    provider_rank=rank,
                    provider_score=score,
                    fused_rank=fused_rank,
                    work=work,
                    raw_record=dict(raw_record),
                )
            )

        reports: list[ProviderReport] = []
        providers_obj = data.get("providers", data.get("provider_reports", []))
        if isinstance(providers_obj, list):
            for item in providers_obj:
                report = _as_mapping(item)
                provider = _first_string(report, ("provider", "name", "id")) or "unknown"
                status = _first_string(report, ("status", "outcome")) or "unknown"
                count = report.get("result_count")
                reports.append(
                    ProviderReport(
                        provider=provider,
                        status=status,
                        result_count=count if isinstance(count, int) else None,
                        reason=_first_string(report, ("reason", "message")),
                    )
                )
        return SearchResponse(
            query=query,
            hits=hits,
            provider_reports=reports,
            raw_envelope=dict(envelope),
        )

    def fetch(self, identifier: str) -> FetchResponse:
        raise CapabilityUnavailable(
            "generic fetch is provider-specific today; discover a gateway fetch operation "
            "and call it explicitly"
        )

    def references(self, identifier: str) -> CitationResponse:
        return self._citations(identifier, "references")

    def cited_by(self, identifier: str) -> CitationResponse:
        return self._citations(identifier, "cited_by")

    def _citations(self, identifier: str, direction: str) -> CitationResponse:
        response = self.client.post(
            "/research/citations", json={"identifier": identifier, "direction": direction}
        )
        response.raise_for_status()
        envelope = response.json()
        if not isinstance(envelope, dict):
            raise GatewayProtocolError("gateway returned a non-object citation envelope")
        data = _as_mapping(envelope.get("data"))
        edge_objects = data.get("edges", [])
        edges: list[CitationEdge] = []
        if isinstance(edge_objects, list):
            for raw_edge in edge_objects:
                edge = _as_mapping(raw_edge)
                source = _as_mapping(edge.get("source"))
                target = _as_mapping(edge.get("target"))
                source_id = _first_string(source, ("raw_id", "id")) or "unknown"
                target_id = _first_string(target, ("raw_id", "id")) or "unknown"
                provider = _first_string(edge, ("provider", "asserting_provider")) or "unknown"
                edges.append(
                    CitationEdge(
                        source_id=source_id,
                        target_id=target_id,
                        provider=provider,
                        provider_edge_id=_first_string(edge, ("edge_id", "id")),
                        metadata=dict(edge),
                    )
                )
        return CitationResponse(identifier=identifier, direction=direction, edges=edges)

    def assets(self, identifier: str) -> AssetResponse:
        raise CapabilityUnavailable("gateway asset discovery is not yet a stable generic operation")
