from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import ProvenanceRecord, RightsStatement, SoftwareIdentity
from discovery.corpus.schema import Asset, IdentifierScheme, Work, WorkIdentifier, WorkVersion
from discovery.retrieval.manifest import GatewayManifest, GatewayOperation, parse_gateway_manifest
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


def _provenance_from_citation(value: object) -> ProvenanceRecord | None:
    citation = _as_mapping(value)
    if not citation:
        return None
    provider = _first_string(citation, ("provider", "source_id")) or "unknown"
    execution = _as_mapping(citation.get("execution"))
    software: SoftwareIdentity | None = None
    software_name = execution.get("software")
    if isinstance(software_name, str) and software_name:
        software = SoftwareIdentity(
            software=software_name,
            software_version=execution.get("software_version")
            if isinstance(execution.get("software_version"), str)
            else None,
            git_commit=execution.get("git_commit")
            if isinstance(execution.get("git_commit"), str)
            else None,
        )
    return ProvenanceRecord(
        provider=provider,
        source_identifier=_first_string(citation, ("source_id",)),
        provider_release=execution.get("provider_release")
        if isinstance(execution.get("provider_release"), str)
        else None,
        request_id=execution.get("request_id")
        if isinstance(execution.get("request_id"), str)
        else None,
        query_fingerprint=execution.get("query_fingerprint")
        if isinstance(execution.get("query_fingerprint"), str)
        else None,
        provider_request_fingerprint=execution.get("provider_request_fingerprint")
        if isinstance(execution.get("provider_request_fingerprint"), str)
        else None,
        response_sha256=execution.get("response_sha256")
        if isinstance(execution.get("response_sha256"), str)
        else None,
        software=software,
    )


def _asset_from_mapping(value: Mapping[str, Any], work_id: str, provider: str) -> Asset:
    rights = _as_mapping(value.get("rights"))
    metadata_rights = _as_mapping(rights.get("metadata"))
    content_rights = _as_mapping(rights.get("content"))
    statement = RightsStatement(
        metadata_license=_first_string(metadata_rights, ("license",)),
        content_license=_first_string(content_rights, ("license",)),
        redistribution=_first_string(content_rights, ("redistribution",)) or "unknown",
        tdm=_first_string(content_rights, ("tdm",)) or "unknown",
        model_training=_first_string(content_rights, ("model_training",)) or "unknown",
        retention=_first_string(content_rights, ("retention",)) or "unknown",
        terms_url=_first_string(content_rights, ("terms_url",)),
    )
    asset_id = _first_string(value, ("asset_id", "id")) or stable_id(
        "asset", f"{work_id}:{provider}:{value.get('canonical_url')}:{value.get('representation')}"
    )
    raw_url = _first_string(value, ("canonical_url", "provider_url", "url"))
    return Asset(
        id=asset_id,
        provider=provider,
        representation=_first_string(value, ("representation", "content_type")) or "unknown",
        url=HttpUrl(raw_url) if raw_url is not None else None,
        mime_type=_first_string(value, ("mime_type", "content_type")),
        availability=_first_string(value, ("availability",)) or "unknown",
        rights=statement,
        checksum=_first_string(value, ("checksum",)),
    )


class GatewayProvider:
    """Client boundary for x402-research-gateway.

    The gateway remains a separate access service. This client discovers its
    feed402 operations rather than duplicating provider-specific implementation
    details in scientific-discovery.
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
        self._manifest: GatewayManifest | None = None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def manifest(self, *, refresh: bool = False) -> GatewayManifest:
        if self._manifest is not None and not refresh:
            return self._manifest
        response = self.client.get("/feed402.json")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise GatewayProtocolError("gateway manifest is not an object")
        self._manifest = parse_gateway_manifest(payload)
        return self._manifest

    def operation(self, operation_id: str) -> GatewayOperation:
        for item in self.manifest().operations:
            if item.operation_id == operation_id:
                return item
        raise CapabilityUnavailable(f"gateway operation not advertised: {operation_id}")

    def invoke(self, operation_id: str, payload: dict[str, object]) -> dict[str, object]:
        operation = self.operation(operation_id)
        if operation.method.upper() == "GET":
            response = self.client.get(
                operation.path, params={key: str(value) for key, value in payload.items()}
            )
        else:
            response = self.client.request(operation.method.upper(), operation.path, json=payload)
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise GatewayProtocolError(f"operation {operation_id} returned a non-object")
        return value

    def estimate_search(self, query: SearchQuery) -> dict[str, object]:
        params: dict[str, str] = {"query": query.text, "limit": str(query.limit)}
        if query.max_cost_usd is not None:
            params["max_cost_usd"] = str(query.max_cost_usd)
        response = self.client.get("/research/federated", params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise GatewayProtocolError("gateway estimate returned a non-object")
        return payload

    def resolve(self, identifier: str) -> dict[str, object]:
        response = self.client.post("/research/resolve", json={"identifier": identifier})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise GatewayProtocolError("gateway resolve returned a non-object")
        return payload

    def search(self, query: SearchQuery) -> SearchResponse:
        payload: dict[str, object] = {"query": query.text, "limit": query.limit}
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
        citations_obj = envelope.get("citation", [])
        citations = citations_obj if isinstance(citations_obj, list) else []
        provider_provenance: dict[str, ProvenanceRecord] = {}
        for value in citations:
            provenance = _provenance_from_citation(value)
            if provenance is not None:
                provider_provenance.setdefault(provenance.provider, provenance)

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
                    provenance=provider_provenance.get(provider),
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
        fetch_ops = self.manifest().operations_for("fetch")
        if len(fetch_ops) != 1:
            raise CapabilityUnavailable(
                "generic fetch is ambiguous; call fetch_with_operation with an advertised operation"
            )
        return self.fetch_with_operation(fetch_ops[0].operation_id, identifier)

    def fetch_with_operation(
        self,
        operation_id: str,
        identifier: str,
        *,
        identifier_field: str = "id",
    ) -> FetchResponse:
        envelope = self.invoke(operation_id, {identifier_field: identifier})
        data = _as_mapping(envelope.get("data"))
        record = _as_mapping(data.get("record", data.get("work", data)))
        self.operation(operation_id)
        provider = operation_id.split("-", 1)[0]
        work = _work_from_record(record, provider) if record else None
        citation_obj = envelope.get("citation")
        citation = citation_obj[0] if isinstance(citation_obj, list) and citation_obj else None
        return FetchResponse(
            provider=provider,
            work=work,
            provenance=_provenance_from_citation(citation),
            raw_envelope=envelope,
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
        reports: list[ProviderReport] = []
        provider_objects = data.get("providers", data.get("provider_reports", []))
        if isinstance(provider_objects, list):
            for raw in provider_objects:
                value = _as_mapping(raw)
                reports.append(
                    ProviderReport(
                        provider=_first_string(value, ("provider", "name")) or "unknown",
                        status=_first_string(value, ("status", "outcome")) or "unknown",
                        result_count=value.get("edge_count")
                        if isinstance(value.get("edge_count"), int)
                        else None,
                        reason=_first_string(value, ("reason",)),
                    )
                )
        return CitationResponse(
            identifier=identifier,
            direction=direction,
            edges=edges,
            provider_reports=reports,
        )

    def assets(self, identifier: str) -> AssetResponse:
        asset_ops = self.manifest().operations_for("assets")
        if len(asset_ops) != 1:
            raise CapabilityUnavailable(
                "generic asset discovery is ambiguous; call assets_with_operation"
            )
        return self.assets_with_operation(asset_ops[0].operation_id, identifier)

    def assets_with_operation(
        self,
        operation_id: str,
        identifier: str,
        *,
        identifier_field: str = "id",
    ) -> AssetResponse:
        envelope = self.invoke(operation_id, {identifier_field: identifier})
        data = _as_mapping(envelope.get("data"))
        raw_assets = data.get("assets", [])
        provider = operation_id.split("-", 1)[0]
        work_id = stable_id("external-work", identifier)
        assets: list[Asset] = []
        if isinstance(raw_assets, list):
            assets = [
                _asset_from_mapping(_as_mapping(item), work_id, provider)
                for item in raw_assets
                if isinstance(item, Mapping)
            ]
        return AssetResponse(identifier=identifier, assets=assets)
