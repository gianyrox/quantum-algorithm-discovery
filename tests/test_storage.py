from __future__ import annotations

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.repositories import WorkRepository


def test_work_upsert_is_identifier_idempotent(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    first = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/example",
        title="First title",
        publication_year=2020,
    )
    second = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/example",
        title="Updated title",
        publication_year=2020,
    )
    with session_scope(factory) as session:
        repo = WorkRepository(session)
        id_one = repo.upsert(first).id
        id_two = repo.upsert(second).id
        assert id_one == id_two
        assert repo.count() == 1
        assert repo.find_by_identifier("doi", "10.1000/example").title == "Updated title"
