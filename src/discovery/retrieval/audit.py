from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from sqlalchemy.orm import Session

from discovery.retrieval.http import HttpCallRecord
from discovery.storage.models import ProviderRequestRow
from discovery.storage.object_store import ObjectStore


def persist_http_call(
    session: Session,
    record: HttpCallRecord,
    body: bytes | None,
    *,
    object_store: ObjectStore | None = None,
    persist_response_bodies: bool = False,
) -> ProviderRequestRow:
    object_key: str | None = None
    if body is not None and persist_response_bodies and object_store is not None:
        media_type = record.response_headers.get("content-type")
        stored = object_store.put(body, media_type=media_type)
        object_key = stored.key
    row = session.get(ProviderRequestRow, record.id)
    if row is None:
        row = ProviderRequestRow(
            id=record.id,
            provider=record.provider,
            operation=record.operation,
            method=record.method,
            url_redacted=record.url,
            request_fingerprint=record.request_fingerprint,
            started_at=record.started_at,
            completed_at=record.completed_at,
            attempts=record.attempts,
            status_code=record.status_code,
            response_sha256=record.response_sha256,
            response_object_key=object_key,
            response_headers_json=record.response_headers,
            error=record.error,
        )
    else:
        row.completed_at = record.completed_at
        row.attempts = record.attempts
        row.status_code = record.status_code
        row.response_sha256 = record.response_sha256
        row.response_object_key = object_key or row.response_object_key
        row.response_headers_json = record.response_headers
        row.error = record.error
    session.add(row)
    session.flush()
    return row


class SqlRequestObserver:
    """Persist final HTTP call metadata for serial request execution only."""

    def __init__(
        self,
        session: Session,
        *,
        object_store: ObjectStore | None = None,
        persist_response_bodies: bool = False,
    ) -> None:
        self.session = session
        self.object_store = object_store
        self.persist_response_bodies = persist_response_bodies

    def __call__(self, record: HttpCallRecord, body: bytes | None) -> None:
        persist_http_call(
            self.session,
            record,
            body,
            object_store=self.object_store,
            persist_response_bodies=self.persist_response_bodies,
        )


@dataclass(frozen=True)
class BufferedHttpCall:
    record: HttpCallRecord
    body: bytes | None


class BufferedRequestObserver:
    """Thread-safe request observer for parallel provider federation.

    HTTP worker threads append immutable records only. The owning SQLAlchemy
    session flushes them later on its own thread, avoiding cross-thread session use.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._items: list[BufferedHttpCall] = []

    def __call__(self, record: HttpCallRecord, body: bytes | None) -> None:
        with self._lock:
            self._items.append(BufferedHttpCall(record=record, body=body))

    def drain(
        self,
        session: Session,
        *,
        object_store: ObjectStore | None = None,
        persist_response_bodies: bool = False,
    ) -> int:
        with self._lock:
            items = self._items
            self._items = []
        for item in items:
            persist_http_call(
                session,
                item.record,
                item.body,
                object_store=object_store,
                persist_response_bodies=persist_response_bodies,
            )
        return len(items)
