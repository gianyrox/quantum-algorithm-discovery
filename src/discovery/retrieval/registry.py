from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.retrieval.gateway_models import GatewaySyncReport
from discovery.retrieval.manifest import GatewayManifest
from discovery.storage.models import ProviderSnapshotRow


class ProviderDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    transport: str
    status: str = "unknown"
    capabilities: list[str] = Field(default_factory=list)
    identifier_schemes: list[str] = Field(default_factory=list)
    metadata_rights: str | None = None
    content_rights: str | None = None
    last_verified: str | None = None
    notes: list[str] = Field(default_factory=list)


class ProviderRegistryService:
    """Local observations of gateway/provider capability state.

    Snapshots are append-only by content fingerprint so a later provider or
    policy change does not rewrite the historical state used by an experiment.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def store_gateway_manifest(self, manifest: GatewayManifest) -> ProviderSnapshotRow:
        fetched = datetime.now(UTC)
        payload = manifest.model_dump(mode="json")
        snapshot_id = stable_id(
            "provider-snapshot",
            f"gateway-manifest:{manifest.spec}:{payload.get('operations')}",
        )
        row = self.session.get(ProviderSnapshotRow, snapshot_id)
        if row is None:
            row = ProviderSnapshotRow(
                id=snapshot_id,
                provider="x402-research-gateway",
                snapshot_type="manifest",
                fetched_at=fetched,
                status="observed",
                capabilities_json=manifest.capabilities,
                payload_json=payload,
            )
            self.session.add(row)
            self.session.flush()
        return row

    def store_sync_report(self, report: GatewaySyncReport) -> list[ProviderSnapshotRow]:
        rows: list[ProviderSnapshotRow] = []
        for provider in report.providers:
            payload = provider.model_dump(mode="json")
            snapshot_id = stable_id(
                "provider-snapshot",
                f"sync:{provider.provider}:{provider.last_verified}:{payload}",
            )
            row = self.session.get(ProviderSnapshotRow, snapshot_id)
            if row is None:
                row = ProviderSnapshotRow(
                    id=snapshot_id,
                    provider=provider.provider,
                    snapshot_type="sync",
                    fetched_at=report.fetched_at,
                    status=provider.status,
                    capabilities_json=provider.capabilities,
                    payload_json=payload,
                )
                self.session.add(row)
                self.session.flush()
            rows.append(row)
        return rows

    def latest(self, provider: str) -> ProviderSnapshotRow | None:
        return self.session.scalar(
            select(ProviderSnapshotRow)
            .where(ProviderSnapshotRow.provider == provider)
            .order_by(ProviderSnapshotRow.fetched_at.desc())
            .limit(1)
        )
