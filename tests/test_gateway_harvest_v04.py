from __future__ import annotations

from collections import deque

from discovery.retrieval.gateway_harvest import (
    GatewayCursorHarvestEngine,
    GatewayCursorHarvestPolicy,
)
from discovery.retrieval.gateway_models import GatewayHarvestPage
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


class FakeGateway:
    name = "x402-research-gateway"

    def __init__(self, pages: list[GatewayHarvestPage]) -> None:
        self.pages = deque(pages)
        self.payloads: list[dict[str, object]] = []

    def harvest_page(self, payload: dict[str, object]) -> GatewayHarvestPage:
        self.payloads.append(payload)
        return self.pages.popleft()


def _record(doi: str, title: str) -> dict[str, object]:
    return {"doi": doi, "title": title, "publication_year": 2025}


def test_gateway_cursor_harvest_resumes_without_replaying_completed_pages(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'gateway-harvest.db'}")
    init_db(engine)
    factory = make_session_factory(engine)

    first_gateway = FakeGateway(
        [
            GatewayHarvestPage(
                provider="crossref",
                records=[_record("10.1000/a", "A")],
                cursor="signed-2",
                exhausted=False,
                cursor_ephemeral=False,
            )
        ]
    )
    with session_scope(factory) as session:
        first = GatewayCursorHarvestEngine(session, first_gateway).execute(
            {"provider": "crossref", "query": "quantum"},
            policy=GatewayCursorHarvestPolicy(max_pages=1),
        )
        assert first.pages == 1
        assert first.records == 1
        assert first.next_cursor == "signed-2"
        assert len(first.unique_work_ids) == 1

    second_gateway = FakeGateway(
        [
            GatewayHarvestPage(
                provider="crossref",
                records=[_record("10.1000/b", "B")],
                cursor=None,
                exhausted=True,
                cursor_ephemeral=False,
            )
        ]
    )
    with session_scope(factory) as session:
        second = GatewayCursorHarvestEngine(session, second_gateway).execute(
            {"provider": "crossref", "query": "quantum"},
            policy=GatewayCursorHarvestPolicy(max_pages=10),
        )
        assert second.pages == 1
        assert second.records == 1
        assert second.exhausted is True
        assert len(second.unique_work_ids) == 2
        assert second_gateway.payloads == [
            {"provider": "crossref", "query": "quantum", "cursor": "signed-2"}
        ]

    third_gateway = FakeGateway([])
    with session_scope(factory) as session:
        third = GatewayCursorHarvestEngine(session, third_gateway).execute(
            {"provider": "crossref", "query": "quantum"}
        )
        assert third.pages == 0
        assert third.exhausted is True
        assert len(third.unique_work_ids) == 2
        assert third_gateway.payloads == []
