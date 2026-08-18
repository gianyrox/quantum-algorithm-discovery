from __future__ import annotations

from discovery.core.provenance import ProvenanceRecord
from discovery.corpus.schema import Author, IdentifierScheme, Work
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import AuthorRow, AuthorshipRow, ProvenanceAssertionRow
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


def test_work_upsert_persists_authorship_and_provenance(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/provenance",
        title="Provenance example",
        authors=[Author(id="author-1", display_name="Ada Researcher")],
        provenance=[
            ProvenanceRecord(provider="crossref", source_identifier="10.1000/provenance")
        ],
    )
    with session_scope(factory) as session:
        row = WorkRepository(session).upsert(work)
        assert session.get(AuthorRow, "author-1") is not None
        authorships = session.query(AuthorshipRow).filter_by(work_id=row.id).all()
        assertions = session.query(ProvenanceAssertionRow).filter_by(subject_id=row.id).all()
        assert len(authorships) == 1
        assert len(assertions) == 1
        assert assertions[0].provider == "crossref"
