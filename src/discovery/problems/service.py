from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from discovery.documents.schema import ParsedDocument
from discovery.problems.extraction import ProblemExtractor
from discovery.problems.schema import ProblemInstance
from discovery.storage.models import ProblemExtractionRunRow
from discovery.storage.repositories import ProblemRepository


class ProblemExtractionService:
    def __init__(self, session: Session, extractor: ProblemExtractor) -> None:
        self.session = session
        self.extractor = extractor
        self.problems = ProblemRepository(session)

    def extract_and_store(
        self,
        document: ParsedDocument,
        *,
        document_id: str | None = None,
    ) -> list[ProblemInstance]:
        run = ProblemExtractionRunRow(
            id=str(uuid4()),
            work_id=document.work_id,
            document_id=document_id,
            extractor=self.extractor.name,
            extractor_version=self.extractor.version,
            status="running",
            problem_count=0,
            started_at=datetime.now(UTC),
            notes_json=[],
        )
        self.session.add(run)
        self.session.flush()
        try:
            problems = self.extractor.extract(document)
            for problem in problems:
                self.problems.upsert(problem)
            run.status = "completed"
            run.problem_count = len(problems)
            run.completed_at = datetime.now(UTC)
            self.session.add(run)
            self.session.flush()
            return problems
        except Exception as exc:
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            run.notes_json = [f"{type(exc).__name__}: {exc}"]
            self.session.add(run)
            self.session.flush()
            raise
