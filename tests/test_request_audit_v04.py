from __future__ import annotations

from datetime import UTC, datetime

from discovery.retrieval.audit import BufferedRequestObserver
from discovery.retrieval.http import HttpCallRecord
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import ProviderRequestRow
from discovery.storage.object_store import LocalContentAddressedStore


def _record(identifier: str) -> HttpCallRecord:
    now = datetime.now(UTC)
    return HttpCallRecord(
        id=identifier,
        provider="fixture",
        operation="search",
        method="GET",
        url="https://example.test/search?q=public&api_key=%3Credacted%3E",
        request_fingerprint=f"sha256:{identifier}",
        started_at=now,
        completed_at=now,
        attempts=1,
        status_code=200,
        response_sha256="sha256:body",
        response_headers={"content-type": "application/json"},
    )


def test_buffered_request_observer_drains_on_session_thread_and_retains_body(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'audit.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    observer = BufferedRequestObserver()
    observer(_record("req-1"), b'{"ok":true}')
    observer(_record("req-2"), b'{"ok":false}')

    with session_scope(factory) as session:
        count = observer.drain(
            session,
            object_store=LocalContentAddressedStore(tmp_path / "objects"),
            persist_response_bodies=True,
        )
        assert count == 2
        assert session.get(ProviderRequestRow, "req-1") is not None
        assert session.get(ProviderRequestRow, "req-1").response_object_key is not None
        assert observer.drain(session) == 0
