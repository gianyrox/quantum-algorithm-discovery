from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse

import httpx
from pydantic import HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset, Author, IdentifierScheme, Work, WorkVersion
from discovery.retrieval.direct.common import identifier, normalize_doi
from discovery.retrieval.http import RequestObserver, ResilientHttpClient, RetryPolicy
from discovery.retrieval.models import (
    AssetResponse,
    CitationResponse,
    FetchResponse,
    ProviderReport,
    RetrievalHit,
    SearchQuery,
    SearchResponse,
)
from discovery.retrieval.paging import SearchPage
from discovery.retrieval.provider import CapabilityUnavailable

_ATOM = "http://www.w3.org/2005/Atom"
_ARXIV = "http://arxiv.org/schemas/atom"
_VERSION = re.compile(r"v\d+$")


def normalize_arxiv_id(value: str) -> str:
    raw = value.strip()
    if "/abs/" in raw:
        raw = urlparse(raw).path.rsplit("/abs/", 1)[-1]
    if raw.casefold().startswith("arxiv:"):
        raw = raw.split(":", 1)[1]
    return _VERSION.sub("", raw)


def _text(node: ET.Element, path: str) -> str | None:
    found = node.find(path)
    if found is None or found.text is None:
        return None
    value = " ".join(found.text.split()).strip()
    return value or None


def _entry_to_work(entry: ET.Element) -> Work | None:
    title = _text(entry, f"{{{_ATOM}}}title")
    entry_id = _text(entry, f"{{{_ATOM}}}id")
    if title is None or entry_id is None:
        return None
    arxiv_id = normalize_arxiv_id(entry_id)
    doi = normalize_doi(_text(entry, f"{{{_ARXIV}}}doi"))
    ids = [
        item
        for item in (
            identifier(IdentifierScheme.ARXIV, arxiv_id, provider="arxiv"),
            identifier(IdentifierScheme.DOI, doi, provider="arxiv"),
        )
        if item is not None
    ]
    published = _text(entry, f"{{{_ATOM}}}published")
    publication_year: int | None = None
    if published:
        try:
            publication_year = datetime.fromisoformat(published.replace("Z", "+00:00")).year
        except ValueError:
            publication_year = None
    authors: list[Author] = []
    for author_node in entry.findall(f"{{{_ATOM}}}author"):
        name = _text(author_node, f"{{{_ATOM}}}name")
        if name:
            authors.append(
                Author(
                    id=stable_id("author", f"arxiv:{name.casefold()}"),
                    display_name=name,
                )
            )
    assets: list[Asset] = []
    for link in entry.findall(f"{{{_ATOM}}}link"):
        href = link.attrib.get("href")
        if not href:
            continue
        rel = link.attrib.get("rel", "alternate")
        link_type = link.attrib.get("type")
        representation = "pdf" if link_type == "application/pdf" else rel
        assets.append(
            Asset(
                id=stable_id("asset", f"arxiv:{arxiv_id}:{representation}:{href}"),
                provider="arxiv",
                representation=representation,
                url=HttpUrl(href),
                mime_type=link_type,
                availability="retrievable",
                rights=RightsStatement(
                    redistribution="unknown",
                    tdm="unknown",
                    model_training="unknown",
                    retention="unknown",
                ),
            )
        )
    primary_category = entry.find(f"{{{_ARXIV}}}primary_category")
    primary_category_term = (
        primary_category.attrib.get("term") if primary_category is not None else None
    )
    return Work(
        id=stable_id("work", f"arxiv:{arxiv_id}"),
        title=title,
        abstract=_text(entry, f"{{{_ATOM}}}summary"),
        publication_year=publication_year,
        work_type="preprint",
        identifiers=ids,
        authors=authors,
        assets=assets,
        version=WorkVersion(
            version_label="preprint",
            provider="arxiv",
            raw_record={"atom_entry": ET.tostring(entry, encoding="unicode")},
        ),
        metadata={
            "published": published,
            "updated": _text(entry, f"{{{_ATOM}}}updated"),
            "primary_category": primary_category_term,
        },
    )


def parse_arxiv_feed(text: str) -> list[Work]:
    root = ET.fromstring(text)
    works: list[Work] = []
    for entry in root.findall(f"{{{_ATOM}}}entry"):
        work = _entry_to_work(entry)
        if work is not None:
            works.append(work)
    return works


class ArxivProvider:
    name = "arxiv"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None = None,
        observer: RequestObserver | None = None,
    ) -> None:
        self.client = client or httpx.Client(
            base_url="https://export.arxiv.org",
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

    def _query(self, params: dict[str, object], operation: str) -> tuple[str, list[Work]]:
        response = self.http.request(
            "GET", "/api/query", provider=self.name, operation=operation, params=params
        )
        response.raise_for_status()
        text = response.text
        return text, parse_arxiv_feed(text)

    def search(self, query: SearchQuery) -> SearchResponse:
        return self.search_page(query).response

    def search_page(
        self,
        query: SearchQuery,
        *,
        cursor: str | None = None,
        page_index: int = 0,
    ) -> SearchPage:
        start = int(cursor) if cursor is not None else 0
        page_size = min(query.limit, 100)
        text, works = self._query(
            {
                "search_query": f'all:"{query.text.replace(chr(34), "")}"',
                "start": start,
                "max_results": page_size,
            },
            "search",
        )
        hits = [
            RetrievalHit(
                provider=self.name,
                provider_rank=rank,
                work=work,
                raw_record=work.version.raw_record if work.version is not None else {},
            )
            for rank, work in enumerate(works[: query.limit], start=1)
        ]
        response = SearchResponse(
            query=query,
            hits=hits,
            provider_reports=[
                ProviderReport(provider=self.name, status="ok", result_count=len(hits))
            ],
            raw_envelope={"atom": text},
        )
        next_cursor = str(start + len(hits)) if len(hits) == page_size else None
        return SearchPage(
            provider=self.name,
            query=query,
            response=response,
            cursor_used=cursor,
            next_cursor=next_cursor,
            exhausted=not bool(next_cursor),
            page_index=page_index,
        )

    def fetch(self, identifier_value: str) -> FetchResponse:
        arxiv_id = normalize_arxiv_id(identifier_value)
        text, works = self._query(
            {"search_query": f"id:{arxiv_id}", "start": 0, "max_results": 1},
            "fetch",
        )
        return FetchResponse(
            provider=self.name,
            work=works[0] if works else None,
            raw_envelope={"atom": text},
        )

    def references(self, identifier_value: str) -> CitationResponse:
        raise CapabilityUnavailable("arXiv Atom API does not expose citation edges")

    def cited_by(self, identifier_value: str) -> CitationResponse:
        raise CapabilityUnavailable("arXiv Atom API does not expose citation edges")

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
