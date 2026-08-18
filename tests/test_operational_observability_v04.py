from __future__ import annotations

from discovery.observability.operations import OperationalObservabilityService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_operational_snapshot_starts_empty(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'operations.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        snapshot = OperationalObservabilityService(session).snapshot()
        assert snapshot.provider_requests == 0
        assert snapshot.documents == 0
        assert snapshot.unresolved_citation_assertions == 0
        assert snapshot.pending_jobs == 0
