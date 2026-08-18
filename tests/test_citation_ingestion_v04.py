from discovery.corpus.citations import CitationIngestionService
from discovery.corpus.schema import IdentifierScheme, Work
from discovery.retrieval.models import CitationEdge
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import CitationRow, ResearchObjectRelationRow
from discovery.storage.repositories import WorkRepository


def test_citations_are_not_misrepresented_as_canonical_work_ids(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'citations.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        repo = WorkRepository(session)
        source = repo.upsert(
            Work.from_primary_identifier(
                scheme=IdentifierScheme.DOI,
                value="10.1000/source",
                title="Source",
            )
        ).id
        service = CitationIngestionService(session)
        report = service.ingest(
            [
                CitationEdge(
                    source_id="10.1000/source",
                    target_id="10.1000/not-yet-ingested",
                    provider="fixture",
                )
            ]
        )
        assert report.unresolved_edges == 1
        assert session.query(CitationRow).count() == 0
        assert session.query(ResearchObjectRelationRow).count() == 1
        target = repo.upsert(
            Work.from_primary_identifier(
                scheme=IdentifierScheme.DOI,
                value="10.1000/not-yet-ingested",
                title="Target",
            )
        ).id
        assert service.materialize_canonical_edges() == 1
        row = session.query(CitationRow).one()
        assert row.source_work_id == source
        assert row.target_work_id == target
