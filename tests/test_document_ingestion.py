import httpx

from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset, IdentifierScheme, Work
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.documents.ingestion import DocumentIngestionService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.object_store import LocalContentAddressedStore
from discovery.storage.repositories import WorkRepository


def test_rights_aware_document_ingestion_persists_raw_and_parsed(tmp_path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text="\\section{Methods}Estimate an eigenvalue.")
    )
    client = httpx.Client(transport=transport)
    fetcher = RightsAwareAssetFetcher(client)
    store = LocalContentAddressedStore(tmp_path / "objects")
    engine = create_database_engine(f"sqlite:///{tmp_path / 'ingestion.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1/ingestion",
        title="Ingestion",
    )
    asset = Asset(
        id="asset-ingestion",
        representation="tex",
        provider="fixture",
        url="https://example.test/source.tex",
        mime_type="application/x-tex",
        availability="retrievable",
        rights=RightsStatement(tdm="allowed", retention="allowed"),
    )
    with session_scope(factory) as session:
        work_id = WorkRepository(session).upsert(work).id
        result = DocumentIngestionService(session, fetcher, store).ingest_asset(
            work_id=work_id,
            asset=asset,
        )
        assert result.stored_object is not None
        assert result.asset.checksum == result.stored_object.sha256
        assert result.document.sections[0].title == "Methods"
