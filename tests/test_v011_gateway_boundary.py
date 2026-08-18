from __future__ import annotations

import pytest

from discovery.retrieval.boundary import GatewayBoundaryError, require_gateway_boundary
from discovery.retrieval.fixture import FixtureProvider
from discovery.retrieval.service import RetrievalService
from discovery.storage.database import create_database_engine, init_db, make_session_factory


class _DirectLikeProvider:
    name = "direct-provider"


def test_gateway_boundary_accepts_offline_fixture_for_tests() -> None:
    report = require_gateway_boundary(FixtureProvider())
    assert report.accepted is True
    assert report.boundary_kind == "fixture"


def test_gateway_boundary_rejects_direct_external_provider() -> None:
    with pytest.raises(GatewayBoundaryError):
        require_gateway_boundary(_DirectLikeProvider())


def test_retrieval_service_enforces_gateway_boundary_by_default(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'boundary.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as session, pytest.raises(GatewayBoundaryError):
        RetrievalService(session, _DirectLikeProvider())  # type: ignore[arg-type]
