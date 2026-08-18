from __future__ import annotations

from discovery.retrieval.gateway_models import GatewaySyncProvider, GatewaySyncReport
from discovery.retrieval.manifest import GatewayManifest, GatewayOperation
from discovery.retrieval.registry import ProviderRegistryService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_provider_registry_preserves_manifest_and_sync_snapshots(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'registry.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    manifest = GatewayManifest(
        spec="feed402/0.3",
        capabilities=["search"],
        operations=[
            GatewayOperation(
                operation_id="crossref-search",
                capability="search",
                path="/research/crossref/search",
            )
        ],
    )
    report = GatewaySyncReport(
        providers=[
            GatewaySyncProvider(
                provider="crossref",
                status="production",
                capabilities=["search", "fetch"],
                last_verified="2026-08-17",
            )
        ]
    )

    with session_scope(factory) as session:
        registry = ProviderRegistryService(session)
        first = registry.store_gateway_manifest(manifest)
        duplicate = registry.store_gateway_manifest(manifest)
        assert first.id == duplicate.id
        sync_rows = registry.store_sync_report(report)
        assert len(sync_rows) == 1
        latest = registry.latest("crossref")
        assert latest is not None
        assert latest.snapshot_type == "sync"
        assert latest.capabilities_json == ["search", "fetch"]
