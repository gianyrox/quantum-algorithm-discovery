from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset, Author, IdentifierScheme, Work, WorkVersion
from discovery.retrieval.direct.common import identifier, normalize_doi
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


def _authors(record: Mapping[str, Any]) -> list[Author]:
    raw_list = record.get("authorList")
    if not isinstance(raw_list, Mapping):
        return []
    raw = raw_list.get("author")
    if not isinstance(raw, list):
        return []
    authors: list[Author] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        name = item.get("fullName")
        if not isinstance(name, str) or not name.strip():
            continue
        raw_author_id = item.get("authorId")
        author_id = raw_author_id if isinstance(raw_author_id, Mapping) else None
        raw_orcid_value = author_id.get("value") if author_id is not None else None
        orcid_value = raw_orcid_value if isinstance(raw_orcid_value, str) else None
        identifiers = {"orcid": orcid_value} if orcid_value else {}
        authors.append(
            Author(
                id=stable_id("author", f"europepmc:{orcid_value or name.casefold()}"),
                display_name=name,
                identifiers=identifiers,
            )
        )
    return authors


def _assets(record: Mapping[str, Any], key: str) -> list[Asset]:
    raw_list = record.get("fullTextUrlList")
    if not isinstance(raw_list, Mapping):
        return []
    raw = raw_list.get("fullTextUrl")
    values = raw if isinstance(raw, list) else []
    assets: list[Asset] = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url:
            continue
        document_style = item.get("documentStyle")
        availability = item.get("availability")
        style = document_style if isinstance(document_style, str) else "fulltext"
        mime = None
        if "pdf" in style.casefold():
            mime = "application/pdf"
        elif "html" in style.casefold():
            mime = "text/html"
        elif "xml" in style.casefold():
            mime = "application/xml"
        assets.append(
            Asset(
                id=stable_id("asset", f"europepmc:{key}:{style}:{url}"),
                provider="europe_pmc",
                representation=style,
                url=HttpUrl(url),
                mime_type=mime,
                availability=(availability if isinstance(availability, str) else "retrievable"),
                rights=RightsStatement(
                    redistribution="unknown",
                    tdm="unknown",
                    model_training="unknown",
                    retention="unknown",
                ),
            )
        )
    return assets


def normalize_europe_pmc_work(record: Mapping[str, Any]) -> Work | None:
    title = record.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    pmid = record.get("pmid") if isinstance(record.get("pmid"), str) else None
    pmcid = record.get("pmcid") if isinstance(record.get("pmcid"), str) else None
    doi = normalize_doi(record.get("doi") if isinstance(record.get("doi"), str) else None)
    source = record.get("source") if isinstance(record.get("source"), str) else None
    ext_id = record.get("id") if isinstance(record.get("id"), str) else record.get("extId")
    ext_id = ext_id if isinstance(ext_id, str) else None
    ids = [
        item
        for item in (
            identifier(IdentifierScheme.DOI, doi, provider="europe_pmc"),
            identifier(IdentifierScheme.PMID, pmid, provider="europe_pmc"),
            identifier(IdentifierScheme.PMCID, pmcid, provider="europe_pmc"),
        )
        if item is not None
    ]
    key = doi or pmid or pmcid or f"{source}:{ext_id}" or title
    year_raw = record.get("pubYear")
    year: int | None = None
    if isinstance(year_raw, int):
        year = year_raw
    elif isinstance(year_raw, str) and year_raw.isdigit():
        year = int(year_raw)
    return Work(
        id=stable_id("work", f"europepmc:{key}"),
        title=title.strip(),
        abstract=(
            record.get("abstractText")
            if isinstance(record.get("abstractText"), str)
            else None
        ),
        publication_year=year,
        work_type=record.get("pubType") if isinstance(record.get("pubType"), str) else None,
        identifiers=ids,
        authors=_authors(record),
        assets=_assets(record, key),
        version=WorkVersion(provider="europe_pmc", raw_record=dict(record)),
        metadata={
            "source": source,
            "ext_id": ext_id,
            "is_open_access": record.get("isOpenAccess"),
            "cited_by_count": record.get("citedByCount"),
            "mesh_heading_list": record.get("meshHeadingList"),
        },
    )


class EuropePMCProvider:
    name = "europe_pmc"

    def __init__(
        self,
        *,
        email: str | None = None,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
        observer: RequestObserver | None = None,
    ) -> None:
        self.email = email
        self.client = client or httpx.Client(
            base_url="https://www.ebi.ac.uk/europepmc/webservices/rest",
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

    def _params(self) -> dict[str, object]:
        return {"email": self.email} if self.email else {}

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
            "query": query.text,
            "format": "json",
            "resultType": "core",
            "pageSize": min(query.limit, 1000),
            **self._params(),
        }
        if cursor:
            params["cursorMark"] = cursor
        payload = self.http.get_json(
            "/search", provider=self.name, operation="search", params=params
        )
        result_list = payload.get("resultList")
        raw = result_list.get("result") if isinstance(result_list, Mapping) else None
        records = raw if isinstance(raw, list) else []
        hits: list[RetrievalHit] = []
        for rank, record in enumerate(records[: query.limit], start=1):
            if not isinstance(record, Mapping):
                continue
            hits.append(
                RetrievalHit(
                    provider=self.name,
                    provider_rank=rank,
                    work=normalize_europe_pmc_work(record),
                    raw_record=dict(record),
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
        raw_next = payload.get("nextCursorMark")
        next_cursor = (
            raw_next
            if isinstance(raw_next, str) and raw_next and raw_next != cursor
            else None
        )
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
        query = f'EXT_ID:"{identifier_value}"'
        response = self.search(SearchQuery(text=query, limit=5))
        exact = next(
            (
                hit
                for hit in response.hits
                if hit.work is not None
                and any(item.value == identifier_value for item in hit.work.identifiers)
            ),
            response.hits[0] if response.hits else None,
        )
        return FetchResponse(
            provider=self.name,
            work=exact.work if exact is not None else None,
            raw_envelope=response.raw_envelope,
        )

    def references(self, identifier_value: str) -> CitationResponse:
        source = "MED"
        raw_id = identifier_value
        if ":" in identifier_value:
            source, raw_id = identifier_value.split(":", 1)
        payload = self.http.get_json(
            f"/{source}/{raw_id}/references",
            provider=self.name,
            operation="references",
            params={"format": "json", "pageSize": 1000, **self._params()},
        )
        ref_list = payload.get("referenceList")
        raw_refs = ref_list.get("reference") if isinstance(ref_list, Mapping) else None
        refs = raw_refs if isinstance(raw_refs, list) else []
        edges: list[CitationEdge] = []
        for item in refs:
            if not isinstance(item, Mapping):
                continue
            target = item.get("id")
            target_source = item.get("source")
            if not isinstance(target, str):
                continue
            rendered = f"{target_source}:{target}" if isinstance(target_source, str) else target
            edges.append(
                CitationEdge(
                    source_id=f"{source}:{raw_id}",
                    target_id=rendered,
                    provider=self.name,
                    metadata=dict(item),
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
        raise CapabilityUnavailable("Europe PMC cited-by is not implemented in the direct adapter")

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
