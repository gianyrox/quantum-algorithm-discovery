from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.documents.extractor import DocumentParser, ParserRegistry
from discovery.documents.parsers import (
    JATSParser,
    LatexParser,
    PlainTextParser,
    SimpleHTMLDocumentParser,
    TEIParser,
)
from discovery.documents.schema import ParsedDocument
from discovery.storage.models import DocumentParseRunRow, DocumentRow


def default_registry() -> ParserRegistry:
    registry = ParserRegistry()
    for parser in (
        PlainTextParser(),
        SimpleHTMLDocumentParser(),
        JATSParser(),
        TEIParser(),
        LatexParser(),
    ):
        registry.register(parser)
    return registry


class DocumentService:
    def __init__(self, session: Session, registry: ParserRegistry | None = None) -> None:
        self.session = session
        self.registry = registry or default_registry()

    def parse_bytes(
        self,
        *,
        work_id: str,
        asset_id: str,
        source_format: str,
        content: bytes,
    ) -> ParsedDocument:
        parser: DocumentParser = self.registry.get(source_format)
        started_at = datetime.now(UTC)
        run = DocumentParseRunRow(
            id=str(uuid4()),
            work_id=work_id,
            asset_id=asset_id,
            parser=parser.name,
            parser_version=parser.version,
            status="running",
            started_at=started_at,
            warnings_json=[],
        )
        self.session.add(run)
        self.session.flush()
        try:
            document = parser.parse(work_id=work_id, asset_id=asset_id, content=content)
            self.store(document)
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.warnings_json = document.warnings
            self.session.add(run)
            self.session.flush()
            return document
        except Exception as exc:
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            run.warnings_json = [f"{type(exc).__name__}: {exc}"]
            self.session.add(run)
            self.session.flush()
            raise

    def parse_file(
        self,
        *,
        work_id: str,
        asset_id: str,
        source_format: str,
        path: Path,
    ) -> ParsedDocument:
        return self.parse_bytes(
            work_id=work_id,
            asset_id=asset_id,
            source_format=source_format,
            content=path.read_bytes(),
        )

    def store(self, document: ParsedDocument) -> DocumentRow:
        document_id = stable_id(
            "document",
            f"{document.work_id}:{document.asset_id}:{document.parser}:{document.parser_version}",
        )
        row = self.session.get(DocumentRow, document_id)
        payload = document.model_dump(mode="json")
        if row is None:
            row = DocumentRow(
                id=document_id,
                work_id=document.work_id,
                asset_id=document.asset_id,
                source_format=document.source_format,
                parser=document.parser,
                parser_version=document.parser_version,
                payload_json=payload,
            )
        else:
            row.payload_json = payload
            row.parser = document.parser
            row.parser_version = document.parser_version
        self.session.add(row)
        self.session.flush()
        return row
