from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from discovery.corpus.schema import Asset
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.storage.models import AssetAcquisitionRow, WorkRow
from discovery.storage.object_store import ObjectStore, StoredObject
from discovery.storage.repositories import AssetRepository


class AssetAcquisitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition_id: str
    work_id: str
    asset: Asset
    stored_object: StoredObject | None = None
    status: str


class AssetAcquisitionService:
    """Rights-aware, audited acquisition of one already-discovered asset."""

    def __init__(
        self,
        session: Session,
        fetcher: RightsAwareAssetFetcher,
        object_store: ObjectStore,
    ) -> None:
        self.session = session
        self.fetcher = fetcher
        self.object_store = object_store

    def acquire(
        self,
        *,
        work_id: str,
        asset: Asset,
        persist_raw: bool = True,
    ) -> AssetAcquisitionResult:
        if self.session.get(WorkRow, work_id) is None:
            raise KeyError(f"unknown canonical work: {work_id}")
        started = datetime.now(UTC)
        acquisition_id = str(uuid4())
        row = AssetAcquisitionRow(
            id=acquisition_id,
            work_id=work_id,
            asset_id=asset.id,
            status="running",
            started_at=started,
            payload_json={"asset": asset.model_dump(mode="json")},
        )
        self.session.add(row)
        self.session.flush()
        try:
            content = self.fetcher.fetch(asset, require_retention=persist_raw)
            stored: StoredObject | None = None
            resolved_asset = asset
            if persist_raw:
                stored = self.object_store.put(content, media_type=asset.mime_type)
                resolved_asset = asset.model_copy(update={"checksum": stored.sha256})
                row.stored_object_key = stored.key
                row.sha256 = stored.sha256
            AssetRepository(self.session).upsert(work_id, resolved_asset)
            row.status = "completed"
            row.completed_at = datetime.now(UTC)
            self.session.add(row)
            self.session.flush()
            return AssetAcquisitionResult(
                acquisition_id=acquisition_id,
                work_id=work_id,
                asset=resolved_asset,
                stored_object=stored,
                status="completed",
            )
        except Exception as exc:
            row.status = "failed"
            row.completed_at = datetime.now(UTC)
            row.error = f"{type(exc).__name__}:{exc}"
            self.session.add(row)
            self.session.flush()
            raise
