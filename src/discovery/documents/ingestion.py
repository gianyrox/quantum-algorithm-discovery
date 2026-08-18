from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from discovery.corpus.schema import Asset
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.documents.schema import ParsedDocument
from discovery.documents.service import DocumentService
from discovery.storage.object_store import ObjectStore, StoredObject
from discovery.storage.repositories import AssetRepository


class DocumentIngestionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_id: str
    asset: Asset
    stored_object: StoredObject | None = None
    document: ParsedDocument


def infer_source_format(asset: Asset) -> str:
    mime = (asset.mime_type or "").casefold()
    representation = asset.representation.casefold()
    if "jats" in mime or "jats" in representation:
        return "jats"
    if "tei" in mime or "tei" in representation:
        return "tei"
    if "tex" in mime or representation in {"tex", "latex", "source"}:
        return "latex"
    if "html" in mime or representation == "html":
        return "html"
    if "text" in mime or representation in {"text", "plain_text", "abstract"}:
        return "text"
    raise ValueError(
        "cannot infer a structured parser format from this asset; provide source_format"
    )


class DocumentIngestionService:
    """Rights-aware bridge from a discovered asset to parsed scientific structure."""

    def __init__(
        self,
        session: Session,
        fetcher: RightsAwareAssetFetcher,
        object_store: ObjectStore,
    ) -> None:
        self.session = session
        self.fetcher = fetcher
        self.object_store = object_store
        self.documents = DocumentService(session)
        self.assets = AssetRepository(session)

    def ingest_asset(
        self,
        *,
        work_id: str,
        asset: Asset,
        source_format: str | None = None,
        persist_raw: bool = True,
    ) -> DocumentIngestionResult:
        content = self.fetcher.fetch(asset, require_retention=persist_raw)
        stored: StoredObject | None = None
        resolved_asset = asset
        if persist_raw:
            stored = self.object_store.put(content, media_type=asset.mime_type)
            resolved_asset = asset.model_copy(update={"checksum": stored.sha256})
        self.assets.upsert(work_id, resolved_asset)
        document = self.documents.parse_bytes(
            work_id=work_id,
            asset_id=asset.id,
            source_format=source_format or infer_source_format(asset),
            content=content,
        )
        return DocumentIngestionResult(
            work_id=work_id,
            asset=resolved_asset,
            stored_object=stored,
            document=document,
        )
