from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset, Author, IdentifierScheme, Work, WorkVersion
from discovery.retrieval.direct.common import clean_markup, identifier, normalize_doi
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
from discovery.retrieval.provider import CapabilityUnavailable


def _first_title(record: Mapping[str, Any]) -> str | None:
    value = record.get("title")
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _year(record: Mapping[str, Any]) -> int | None:
    for key in ("published-print", "published-online", "published", "issued"):
        value = record.get(key)
        if not isinstance(value, Mapping):
            continue
        parts = value.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            year = parts[0][0]
            if isinstance(year, int):
                return year
    return None


def _authors(record: Mapping[str, Any]) -> list[Author]:
    raw = record.get("author")
    if not isinstance(raw, list):
        return []
    authors: list[Author] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        raw_given = item.get("given")
        raw_family = item.get("family")
        given = raw_given if isinstance(raw_given, str) else ""
        family = raw_family if isinstance(raw_family, str) else ""
        name = " ".join(part for part in (given.strip(), family.strip()) if part).strip()
        if not name:
            continue
        orcid = item.get("ORCID") if isinstance(item.get("ORCID"), str) else None
        identifiers = {"orcid": orcid.rsplit("/", 1)[-1]} if orcid else {}
        authors.append(
            Author(
                id=stable_id("author", f"crossref:{orcid or name.casefold()}"),
                display_name=name,
                identifiers=identifiers,
            )
        )
    return authors


def _assets(record: Mapping[str, Any], doi: str | None) -> list[Asset]:
    raw = record.get("link")
    if not isinstance(raw, list):
        return []
    assets: list[Asset] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        url = item.get("URL")
        if not isinstance(url, str) or not url:
            continue
        content_type = item.get("content-type")
        mime = content_type if isinstance(content_type, str) else None
        representation = "fulltext" if mime else "link"
        assets.append(
            Asset(
                id=stable_id("asset", f"crossref:{doi or 'unknown'}:{url}"),
                provider="crossref",
                representation=representation,
                url=HttpUrl(url),
                mime_type=mime,
                availability="retrievable",
                rights=RightsStatement(
                    metadata_license="crossref-rest-metadata",
                    redistribution="unknown",
                    tdm="unknown",
                    model_training="unknown",
                    retention="unknown",
                ),
            )
        )
    return assets


def normalize_crossref_work(record: Mapping[str, Any]) -> Work | None:
    title = _first_title(record)
    if title is None:
        return None
    doi = normalize_doi(record.get("DOI") if isinstance(record.get("DOI"), str) else None)
    ids = [item for item in [identifier(IdentifierScheme.DOI, doi, provider="crossref")] if item]
    primary = doi or str(record.get("URL") or title)
    work_type = record.get("type")
    language = record.get("language")
    return Work(
        id=stable_id("work", f"crossref:{primary}"),
        title=title,
        abstract=clean_markup(
            record.get("abstract") if isinstance(record.get("abstract"), str) else None
        ),
        publication_year=_year(record),
        work_type=work_type if isinstance(work_type, str) else None,
        primary_language=language if isinstance(language, str) else None,
        identifiers=ids,
        authors=_authors(record),
        assets=_assets(record, doi),
        version=WorkVersion(provider="crossref", raw_record=dict(record)),
        metadata={
            "container_title": record.get("container-title"),
            "publisher": record.get("publisher"),
            "subject": record.get("subject"),
        },
    )


class CrossrefProvider:
    name = "crossref"

    def __init__(
        self,
        *,
        mailto: str | None = None,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
        observer: RequestObserver | None = None,
    ) -> None:
        self.mailto = mailto
        headers = {"User-Agent": "scientific-discovery/0.4"}
        if mailto:
            headers["User-Agent"] = f"scientific-discovery/0.4 (mailto:{mailto})"
        self.client = client or httpx.Client(
            base_url="https://api.crossref.org",
            timeout=30.0,
            follow_redirects=True,
            headers=headers,
        )
        self._owns_client = client is None
        self.http = ResilientHttpClient(
            self.client, retry_policy=retry_policy, observer=observer
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _params(self) -> dict[str, object]:
        return {"mailto": self.mailto} if self.mailto else {}

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
            "query.bibliographic": query.text,
            "rows": min(query.limit, 1000),
            "cursor": cursor or "*",
            **self._params(),
        }
        provider_filter = query.filters.get("crossref_filter")
        if isinstance(provider_filter, str) and provider_filter:
            params["filter"] = provider_filter
        payload = self.http.get_json(
            "/works", provider=self.name, operation="search", params=params
        )
        message = payload.get("message")
        items = message.get("items") if isinstance(message, Mapping) else None
        records = items if isinstance(items, list) else []
        hits: list[RetrievalHit] = []
        for rank, raw in enumerate(records[: query.limit], start=1):
            if not isinstance(raw, Mapping):
                continue
            hits.append(
                RetrievalHit(
                    provider=self.name,
                    provider_rank=rank,
                    work=normalize_crossref_work(raw),
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
        raw_next = message.get("next-cursor") if isinstance(message, Mapping) else None
        next_cursor = raw_next if isinstance(raw_next, str) and raw_next else None
        return SearchPage(
            provider=self.name,
            query=query,
            response=response,
            cursor_used=cursor,
            next_cursor=next_cursor,
            exhausted=not bool(next_cursor) or not hits,
            page_index=page_index,
        )

    def fetch(self, identifier_value: str) -> FetchResponse:
        doi = normalize_doi(identifier_value)
        if doi is None:
            raise ValueError("Crossref fetch requires a DOI")
        payload = self.http.get_json(
            f"/works/{quote(doi, safe='')}",
            provider=self.name,
            operation="fetch",
            params=self._params(),
        )
        raw = payload.get("message")
        record = raw if isinstance(raw, Mapping) else {}
        return FetchResponse(
            provider=self.name,
            work=normalize_crossref_work(record),
            raw_envelope=payload,
        )

    def references(self, identifier_value: str) -> CitationResponse:
        response = self.fetch(identifier_value)
        work = response.work
        record = work.version.raw_record if work is not None and work.version is not None else {}
        doi = normalize_doi(identifier_value) or identifier_value
        raw_refs = record.get("reference")
        refs = raw_refs if isinstance(raw_refs, list) else []
        edges: list[CitationEdge] = []
        for index, raw in enumerate(refs):
            if not isinstance(raw, Mapping):
                continue
            target_doi = normalize_doi(raw.get("DOI") if isinstance(raw.get("DOI"), str) else None)
            if target_doi:
                target = target_doi
            else:
                unstructured = raw.get("unstructured")
                if not isinstance(unstructured, str) or not unstructured.strip():
                    continue
                target = stable_id("crossref-reference", unstructured.strip())
            edges.append(
                CitationEdge(
                    source_id=doi,
                    target_id=target,
                    provider=self.name,
                    provider_edge_id=f"{doi}:{index}",
                    metadata=dict(raw),
                )
            )
        return CitationResponse(
            identifier=identifier_value,
            direction="references",
            edges=edges,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(edges))
            ],
        )

    def cited_by(self, identifier_value: str) -> CitationResponse:
        raise CapabilityUnavailable("Crossref REST does not expose a general cited-by listing")

    def assets(self, identifier_value: str) -> AssetResponse:
        response = self.fetch(identifier_value)
        assets = response.work.assets if response.work is not None else []
        return AssetResponse(
            identifier=identifier_value,
            assets=assets,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(assets))
            ],
        )
