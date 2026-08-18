from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from discovery.corpus.schema import Asset
from discovery.documents.schema import ParsedDocument
from discovery.documents.service import DocumentService
from discovery.mathematics.service import MathematicsService
from discovery.problems.baseline_extractor import TransparentBaselineProblemExtractor
from discovery.problems.service import ProblemExtractionService
from discovery.storage.models import AssetRow, WorkRow
from discovery.storage.repositories import AssetRepository


class CanonicalProcessingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_id: str
    asset_id: str
    document_id: str
    equation_count: int = Field(ge=0)
    problem_ids: list[str] = Field(default_factory=list)


class CanonicalResearchProcessor:
    """Process supplied content only after canonical Work/Asset links exist."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def process_bytes(
        self,
        *,
        work_id: str,
        asset: Asset,
        source_format: str,
        content: bytes,
    ) -> CanonicalProcessingResult:
        if self.session.get(WorkRow, work_id) is None:
            raise KeyError(f"unknown canonical work: {work_id}")
        existing_asset = self.session.get(AssetRow, asset.id)
        if existing_asset is not None and existing_asset.work_id != work_id:
            raise ValueError(
                f"asset {asset.id} belongs to {existing_asset.work_id}, not {work_id}"
            )
        AssetRepository(self.session).upsert(work_id, asset)
        documents = DocumentService(self.session)
        document: ParsedDocument = documents.parse_bytes(
            work_id=work_id,
            asset_id=asset.id,
            source_format=source_format,
            content=content,
        )
        document_row = documents.store(document)
        expressions = MathematicsService(self.session).from_document(
            document,
            document_id=document_row.id,
        )
        problems = ProblemExtractionService(
            self.session,
            TransparentBaselineProblemExtractor(),
        ).extract_and_store(document, document_id=document_row.id)
        return CanonicalProcessingResult(
            work_id=work_id,
            asset_id=asset.id,
            document_id=document_row.id,
            equation_count=len(expressions),
            problem_ids=[item.id for item in problems],
        )
