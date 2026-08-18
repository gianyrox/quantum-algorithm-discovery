from __future__ import annotations

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.retrieval.deep_harvest import DeepHarvestEngine, DeepHarvestPolicy
from discovery.retrieval.models import (
    AssetResponse,
    CitationResponse,
    FetchResponse,
    RetrievalHit,
    SearchQuery,
    SearchResponse,
)
from discovery.retrieval.paging import SearchPage
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import WorkRow


class PagedFixtureProvider:
    name = "paged-fixture"

    def __init__(self) -> None:
        self.calls = 0

    def search_page(
        self,
        query: SearchQuery,
        *,
        cursor: str | None = None,
        page_index: int = 0,
    ) -> SearchPage:
        self.calls += 1
        index = int(cursor or "0")
        work = Work.from_primary_identifier(
            scheme=IdentifierScheme.DOI,
            value=f"10.1000/page-{index}",
            title=f"Page {index}",
        )
        response = SearchResponse(
            query=query,
            hits=[RetrievalHit(provider=self.name, provider_rank=1, work=work)],
        )
        next_cursor = str(index + 1) if index < 2 else None
        return SearchPage(
            provider=self.name,
            query=query,
            response=response,
            cursor_used=cursor,
            next_cursor=next_cursor,
            exhausted=next_cursor is None,
            page_index=page_index,
        )

    def search(self, query: SearchQuery) -> SearchResponse:
        return self.search_page(query).response

    def fetch(self, identifier: str) -> FetchResponse:
        return FetchResponse(provider=self.name, work=None)

    def references(self, identifier: str) -> CitationResponse:
        return CitationResponse(identifier=identifier, direction="references", edges=[])

    def cited_by(self, identifier: str) -> CitationResponse:
        return CitationResponse(identifier=identifier, direction="cited_by", edges=[])

    def assets(self, identifier: str) -> AssetResponse:
        return AssetResponse(identifier=identifier, assets=[])


def test_deep_harvest_pages_and_resumes_without_replaying_completed_pages(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'deep.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    provider = PagedFixtureProvider()
    query = SearchQuery(text="spectral", limit=1)
    with session_scope(factory) as session:
        first = DeepHarvestEngine(session, provider).execute(
            query,
            policy=DeepHarvestPolicy(max_pages=2),
        )
        assert first.pages == 2
        assert first.next_cursor == "2"
        assert session.query(WorkRow).count() == 2
    with session_scope(factory) as session:
        second = DeepHarvestEngine(session, provider).execute(
            query,
            policy=DeepHarvestPolicy(max_pages=5),
        )
        assert second.pages == 1
        assert second.exhausted is True
        assert session.query(WorkRow).count() == 3
    assert provider.calls == 3
