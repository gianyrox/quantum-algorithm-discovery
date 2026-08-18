from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset, Author, IdentifierScheme, Work, WorkVersion
from discovery.retrieval.direct.common import (
    as_mapping,
    identifier,
    normalize_doi,
    normalize_openalex_id,
)
from discovery.retrieval.http import RequestObserver, ResilientHttpClient, RetryPolicy
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
from discovery.retrieval.paging import SearchPage


def _abstract_from_inverted_index(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    positions: list[tuple[int, str]] = []
    for token, raw_positions in value.items():
        if not isinstance(token, str) or not isinstance(raw_positions, list):
            continue
        for position in raw_positions:
            if isinstance(position, int):
                positions.append((position, token))
    if not positions:
        return None
    return " ".join(token for _, token in sorted(positions))


def _authors(record: Mapping[str, Any]) -> list[Author]:
    raw = record.get("authorships")
    if not isinstance(raw, list):
        return []
    authors: list[Author] = []
    for item in raw:
        authorship = as_mapping(item)
        author = as_mapping(authorship.get("author"))
        name = author.get("display_name")
        if not isinstance(name, str) or not name.strip():
            continue
        author_id = author.get("id") if isinstance(author.get("id"), str) else None
        identifiers: dict[str, str] = {}
        orcid = author.get("orcid")
        if isinstance(orcid, str) and orcid:
            identifiers["orcid"] = orcid.rsplit("/", 1)[-1]
        authors.append(
            Author(
                id=normalize_openalex_id(author_id) or stable_id("author", f"openalex:{name}"),
                display_name=name,
                identifiers=identifiers,
            )
        )
    return authors


def _assets(record: Mapping[str, Any]) -> list[Asset]:
    work_id = normalize_openalex_id(record.get("id") if isinstance(record.get("id"), str) else None)
    key = work_id or str(record.get("id") or record.get("doi") or record.get("title") or "unknown")
    assets: list[Asset] = []
    seen_urls: set[str] = set()
    locations = [record.get("primary_location")]
    best_oa = record.get("best_oa_location")
    if best_oa is not None:
        locations.append(best_oa)
    for raw in locations:
        location = as_mapping(raw)
        for field, representation in (("pdf_url", "pdf"), ("landing_page_url", "landing_page")):
            url = location.get(field)
            if not isinstance(url, str) or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            assets.append(
                Asset(
                    id=stable_id("asset", f"openalex:{key}:{representation}:{url}"),
                    provider="openalex",
                    representation=representation,
                    url=HttpUrl(url),
                    mime_type="application/pdf" if representation == "pdf" else "text/html",
                    availability="retrievable",
                    rights=RightsStatement(
                        metadata_license="CC0",
                        redistribution="unknown",
                        tdm="unknown",
                        model_training="unknown",
                        retention="unknown",
                    ),
                )
            )
    return assets


def normalize_openalex_work(record: Mapping[str, Any]) -> Work | None:
    title = record.get("display_name", record.get("title"))
    if not isinstance(title, str) or not title.strip():
        return None
    openalex_id = normalize_openalex_id(
        record.get("id") if isinstance(record.get("id"), str) else None
    )
    ids = as_mapping(record.get("ids"))
    doi = normalize_doi(
        ids.get("doi") if isinstance(ids.get("doi"), str) else record.get("doi")
        if isinstance(record.get("doi"), str)
        else None
    )
    work_identifiers = [
        item
        for item in (
            identifier(IdentifierScheme.OPENALEX, openalex_id, provider="openalex"),
            identifier(IdentifierScheme.DOI, doi, provider="openalex"),
            identifier(
                IdentifierScheme.PMID,
                ids.get("pmid") if isinstance(ids.get("pmid"), str) else None,
                provider="openalex",
            ),
            identifier(
                IdentifierScheme.PMCID,
                ids.get("pmcid") if isinstance(ids.get("pmcid"), str) else None,
                provider="openalex",
            ),
        )
        if item is not None
    ]
    primary = work_identifiers[0].value if work_identifiers else title
    year = record.get("publication_year")
    work_type = record.get("type")
    language = record.get("language")
    return Work(
        id=stable_id("work", f"openalex:{primary}"),
        title=title.strip(),
        abstract=_abstract_from_inverted_index(record.get("abstract_inverted_index")),
        publication_year=year if isinstance(year, int) else None,
        work_type=work_type if isinstance(work_type, str) else None,
        primary_language=language if isinstance(language, str) else None,
        identifiers=work_identifiers,
        authors=_authors(record),
        assets=_assets(record),
        version=WorkVersion(provider="openalex", raw_record=dict(record)),
        metadata={
            "cited_by_count": record.get("cited_by_count"),
            "open_access": record.get("open_access"),
            "topics": record.get("topics"),
        },
    )


class OpenAlexProvider:
    name = "openalex"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        mailto: str | None = None,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
        observer: RequestObserver | None = None,
    ) -> None:
        self.api_key = api_key
        self.mailto = mailto
        self.client = client or httpx.Client(
            base_url="https://api.openalex.org",
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "scientific-discovery/0.4"},
        )
        self._owns_client = client is None
        self.http = ResilientHttpClient(
            self.client, retry_policy=retry_policy, observer=observer
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _auth_params(self) -> dict[str, object]:
        params: dict[str, object] = {}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto
        return params

    def search(self, query: SearchQuery) -> SearchResponse:
        return self.search_page(query).response

    def search_page(
        self,
        query: SearchQuery,
        *,
        cursor: str | None = None,
        page_index: int = 0,
    ) -> SearchPage:
        params: dict[str, object] = {
            "search": query.text,
            "per-page": min(query.limit, 100),
            "cursor": cursor or "*",
            **self._auth_params(),
        }
        provider_filter = query.filters.get("openalex_filter")
        if isinstance(provider_filter, str) and provider_filter:
            params["filter"] = provider_filter
        payload = self.http.get_json(
            "/works", provider=self.name, operation="search", params=params
        )
        raw_results = payload.get("results")
        results = raw_results if isinstance(raw_results, list) else []
        hits: list[RetrievalHit] = []
        for rank, raw in enumerate(results[: query.limit], start=1):
            if not isinstance(raw, Mapping):
                continue
            work = normalize_openalex_work(raw)
            hits.append(
                RetrievalHit(
                    provider=self.name,
                    provider_rank=rank,
                    work=work,
                    raw_record=dict(raw),
                )
            )
        response = SearchResponse(
            query=query,
            hits=hits,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(hits))
            ],
            raw_envelope=payload,
        )
        meta = payload.get("meta")
        next_cursor = meta.get("next_cursor") if isinstance(meta, Mapping) else None
        rendered_cursor = next_cursor if isinstance(next_cursor, str) and next_cursor else None
        return SearchPage(
            provider=self.name,
            query=query,
            response=response,
            cursor_used=cursor,
            next_cursor=rendered_cursor,
            exhausted=not bool(rendered_cursor) or not hits,
            page_index=page_index,
        )

    def _fetch_record(self, identifier_value: str) -> Mapping[str, Any] | None:
        normalized = identifier_value.strip()
        if normalized.casefold().startswith("10.") or "doi.org/" in normalized.casefold():
            doi = normalize_doi(normalized)
            path_id = f"https://doi.org/{doi}" if doi else normalized
        else:
            path_id = normalize_openalex_id(normalized) or normalized
        payload = self.http.get_json(
            f"/works/{quote(path_id, safe='')}",
            provider=self.name,
            operation="fetch",
            params=self._auth_params(),
        )
        return payload

    def fetch(self, identifier_value: str) -> FetchResponse:
        record = self._fetch_record(identifier_value)
        work = normalize_openalex_work(record) if record is not None else None
        return FetchResponse(provider=self.name, work=work, raw_envelope=dict(record or {}))

    def references(self, identifier_value: str) -> CitationResponse:
        record = self._fetch_record(identifier_value)
        if record is None:
            return CitationResponse(identifier=identifier_value, direction="references", edges=[])
        source_id = normalize_openalex_id(
            record.get("id") if isinstance(record.get("id"), str) else None
        ) or identifier_value
        refs = record.get("referenced_works")
        values = refs if isinstance(refs, list) else []
        edges = [
            CitationEdge(
                source_id=source_id,
                target_id=normalize_openalex_id(value) or value,
                provider=self.name,
            )
            for value in values
            if isinstance(value, str)
        ]
        return CitationResponse(
            identifier=identifier_value,
            direction="references",
            edges=edges,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(edges))
            ],
        )

    def cited_by(self, identifier_value: str) -> CitationResponse:
        record = self._fetch_record(identifier_value)
        if record is None:
            return CitationResponse(identifier=identifier_value, direction="cited_by", edges=[])
        target_id = normalize_openalex_id(
            record.get("id") if isinstance(record.get("id"), str) else None
        )
        if target_id is None:
            return CitationResponse(identifier=identifier_value, direction="cited_by", edges=[])
        payload = self.http.get_json(
            "/works",
            provider=self.name,
            operation="cited_by",
            params={"filter": f"cites:{target_id}", "per-page": 100, **self._auth_params()},
        )
        raw_results = payload.get("results")
        results = raw_results if isinstance(raw_results, list) else []
        edges: list[CitationEdge] = []
        for raw in results:
            if not isinstance(raw, Mapping):
                continue
            source_id = normalize_openalex_id(
                raw.get("id") if isinstance(raw.get("id"), str) else None
            )
            if source_id:
                edges.append(
                    CitationEdge(source_id=source_id, target_id=target_id, provider=self.name)
                )
        return CitationResponse(
            identifier=identifier_value,
            direction="cited_by",
            edges=edges,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(edges))
            ],
        )

    def assets(self, identifier_value: str) -> AssetResponse:
        record = self._fetch_record(identifier_value)
        assets = _assets(record) if record is not None else []
        return AssetResponse(
            identifier=identifier_value,
            assets=assets,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(assets))
            ],
        )
