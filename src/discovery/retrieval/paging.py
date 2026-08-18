from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from discovery.retrieval.models import SearchQuery, SearchResponse
from discovery.retrieval.provider import ResearchProvider


class SearchPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    query: SearchQuery
    response: SearchResponse
    cursor_used: str | None = None
    next_cursor: str | None = None
    exhausted: bool = False
    page_index: int = Field(default=0, ge=0)


class PagedResearchProvider(ResearchProvider, Protocol):
    def search_page(
        self,
        query: SearchQuery,
        *,
        cursor: str | None = None,
        page_index: int = 0,
    ) -> SearchPage: ...
