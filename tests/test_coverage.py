from discovery.observability.coverage import CoverageService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_coverage_snapshot_reports_empty_corpus(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'coverage.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        snapshot = CoverageService(session).snapshot()
        assert snapshot.metrics["works"] == 0
        assert any(item["dimension"] == "corpus" for item in snapshot.gaps)
