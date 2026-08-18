from __future__ import annotations

import httpx

from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset, IdentifierScheme, Work
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.execution.queue import ProcessingQueue
from discovery.execution.schema import ProcessingStage
from discovery.execution.worker import LocalProcessingWorker
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import AssetRow, DocumentRow, ProblemInstanceRow
from discovery.storage.object_store import LocalContentAddressedStore
from discovery.storage.repositories import AssetRepository, WorkRepository


def test_local_worker_acquires_structured_asset_and_processes_canonical_work(tmp_path) -> None:
    latex = b"""\\section{Method}\nWe solve an eigenvalue problem $A x = \\lambda x$.\n"""

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.test/paper.tex"
        return httpx.Response(200, content=latex, headers={"content-type": "text/x-tex"})

    engine = create_database_engine(f"sqlite:///{tmp_path / 'worker.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = RightsAwareAssetFetcher(client=client)
    store = LocalContentAddressedStore(tmp_path / "objects")
    try:
        with session_scope(factory) as session:
            work_id = WorkRepository(session).upsert(
                Work.from_primary_identifier(
                    scheme=IdentifierScheme.DOI,
                    value="10.1000/worker",
                    title="Worker test",
                )
            ).id
            asset = Asset(
                id="asset-worker-tex",
                representation="tex",
                provider="fixture",
                url="https://example.test/paper.tex",
                mime_type="text/x-tex",
                availability="retrievable",
                rights=RightsStatement(tdm="allowed", retention="allowed"),
            )
            AssetRepository(session).upsert(work_id, asset)
            ProcessingQueue(session).enqueue(
                work_id=work_id,
                asset_id=asset.id,
                stage=ProcessingStage.ASSET_ACQUISITION,
                payload={"source_format": "latex"},
            )
            result = LocalProcessingWorker(session, store, fetcher).run_once()
            assert result.status == "completed"
            assert session.get(AssetRow, asset.id).checksum is not None
            assert session.query(DocumentRow).count() == 1
            assert session.query(ProblemInstanceRow).count() >= 1
            assert ProcessingQueue(session).stats().completed == 1
    finally:
        fetcher.close()
