from __future__ import annotations

from pydantic import BaseModel, ConfigDict, HttpUrl
from sqlalchemy.orm import Session

from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset
from discovery.documents.acquisition import AssetAcquisitionService
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.documents.ingestion import infer_source_format
from discovery.execution.processing import CanonicalResearchProcessor
from discovery.execution.queue import ProcessingQueue
from discovery.execution.schema import ProcessingStage
from discovery.storage.models import AssetRow
from discovery.storage.object_store import ObjectStore


class WorkerResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str | None = None
    status: str
    detail: str | None = None


def asset_from_row(row: AssetRow) -> Asset:
    rights = RightsStatement.model_validate(row.rights_json) if row.rights_json else None
    return Asset(
        id=row.id,
        provider=row.provider,
        representation=row.representation,
        url=HttpUrl(row.url) if row.url is not None else None,
        mime_type=row.mime_type,
        availability=row.availability,
        rights=rights,
        checksum=row.checksum,
    )


class LocalProcessingWorker:
    """Single-process worker for rights-aware structured document processing.

    It deliberately handles only stages with deterministic local behavior. Asset
    discovery and provider-side identity/integrity remain retrieval/gateway work.
    """

    def __init__(
        self,
        session: Session,
        object_store: ObjectStore,
        fetcher: RightsAwareAssetFetcher,
    ) -> None:
        self.session = session
        self.object_store = object_store
        self.fetcher = fetcher
        self.queue = ProcessingQueue(session)

    def run_once(self) -> WorkerResult:
        job = self.queue.claim_next(stages=[ProcessingStage.ASSET_ACQUISITION])
        if job is None:
            return WorkerResult(status="idle")
        if job.asset_id is None:
            failed = self.queue.fail(job.id, "asset acquisition job has no asset_id")
            return WorkerResult(job_id=job.id, status=failed.status, detail=failed.error)
        row = self.session.get(AssetRow, job.asset_id)
        if row is None or row.work_id != job.work_id:
            failed = self.queue.fail(job.id, f"unknown asset for work: {job.asset_id}")
            return WorkerResult(job_id=job.id, status=failed.status, detail=failed.error)
        asset = asset_from_row(row)
        try:
            acquisition = AssetAcquisitionService(
                self.session,
                self.fetcher,
                self.object_store,
            ).acquire(work_id=job.work_id, asset=asset, persist_raw=True)
            if acquisition.stored_object is None:
                raise RuntimeError("acquisition did not retain a raw object")
            content = self.object_store.get(acquisition.stored_object.key)
            source_format = str(job.payload.get("source_format") or infer_source_format(asset))
            processed = CanonicalResearchProcessor(self.session).process_bytes(
                work_id=job.work_id,
                asset=acquisition.asset,
                source_format=source_format,
                content=content,
            )
            self.queue.complete(job.id)
            return WorkerResult(
                job_id=job.id,
                status="completed",
                detail=(
                    f"document={processed.document_id} equations={processed.equation_count} "
                    f"problems={len(processed.problem_ids)}"
                ),
            )
        except Exception as exc:
            failed = self.queue.fail(job.id, f"{type(exc).__name__}:{exc}")
            return WorkerResult(job_id=job.id, status=failed.status, detail=failed.error)
