from __future__ import annotations

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.retrieval.fixture import FixtureProvider
from discovery.retrieval.models import RetrievalHit, SearchQuery
from discovery.retrieval.service import RetrievalService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.repositories import WorkRepository


def test_retrieval_service_persists_run_and_work(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/retrieved",
        title="Retrieved work",
    )
    provider = FixtureProvider(
        hits=[RetrievalHit(provider="fixture", provider_rank=1, work=work, raw_record={"x": 1})]
    )
    with session_scope(factory) as session:
        response = RetrievalService(session, provider).execute(SearchQuery(text="retrieval"))
        assert len(response.hits) == 1
        assert WorkRepository(session).count() == 1
