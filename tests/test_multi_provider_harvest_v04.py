from __future__ import annotations

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.retrieval.coordinator import DirectHarvestCoordinator, MultiProviderHarvestPolicy
from discovery.retrieval.models import RetrievalHit, SearchQuery, SearchResponse
from discovery.retrieval.paging import SearchPage
from discovery.retrieval.provider import CapabilityUnavailable
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


class OnePageProvider:
    def __init__(self, name: str, doi: str) -> None:
        self.name = name
        self.doi = doi

    def search_page(
        self,
        query: SearchQuery,
        *,
        cursor: str | None,
        page_index: int,
    ) -> SearchPage:
        assert cursor is None
        work = Work.from_primary_identifier(
            scheme=IdentifierScheme.DOI,
            value=self.doi,
            title=f"{self.name} result",
        )
        return SearchPage(
            provider=self.name,
            query=query,
            response=SearchResponse(
                query=query,
                hits=[RetrievalHit(provider=self.name, provider_rank=1, work=work)],
            ),
            exhausted=True,
        )

    def search(self, query: SearchQuery) -> SearchResponse:
        return self.search_page(query, cursor=None, page_index=0).response

    def fetch(self, identifier: str):
        raise CapabilityUnavailable(identifier)

    def references(self, identifier: str):
        raise CapabilityUnavailable(identifier)

    def cited_by(self, identifier: str):
        raise CapabilityUnavailable(identifier)

    def assets(self, identifier: str):
        raise CapabilityUnavailable(identifier)


def test_multi_provider_harvest_unions_provider_specific_deep_results(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'multi.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        result = DirectHarvestCoordinator(session).execute(
            SearchQuery(text="same query", limit=100),
            {
                "alpha": OnePageProvider("alpha", "10.1000/a"),
                "beta": OnePageProvider("beta", "10.1000/b"),
            },
            policy=MultiProviderHarvestPolicy(max_pages_per_provider=2),
        )
        assert result.total_pages == 2
        assert result.total_hits == 2
        assert len(result.unique_work_ids) == 2
        assert result.errors == []
