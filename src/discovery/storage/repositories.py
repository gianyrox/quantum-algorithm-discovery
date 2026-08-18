from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.corpus.schema import Work
from discovery.problems.schema import ProblemInstance
from discovery.storage.models import (
    ProblemInstanceRow,
    WorkIdentifierRow,
    WorkRow,
    WorkVersionRow,
)


class WorkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_identifier(self, scheme: str, value: str) -> WorkRow | None:
        stmt = (
            select(WorkRow)
            .join(WorkIdentifierRow, WorkIdentifierRow.work_id == WorkRow.id)
            .where(WorkIdentifierRow.scheme == scheme, WorkIdentifierRow.value == value)
        )
        return self.session.scalar(stmt)

    def upsert(self, work: Work) -> WorkRow:
        existing: WorkRow | None = None
        for identifier in work.identifiers:
            existing = self.find_by_identifier(identifier.scheme.value, identifier.value)
            if existing is not None:
                break

        now = datetime.now(UTC)
        work_id = existing.id if existing else work.id
        row = existing or WorkRow(
            id=work_id,
            title=work.title,
            created_at=now,
            updated_at=now,
        )
        row.title = work.title
        row.abstract = work.abstract
        row.publication_year = work.publication_year
        row.work_type = work.work_type
        row.primary_language = work.primary_language
        row.metadata_json = work.metadata
        row.updated_at = now
        self.session.add(row)
        self.session.flush()

        for identifier in work.identifiers:
            found = self.session.scalar(
                select(WorkIdentifierRow).where(
                    WorkIdentifierRow.scheme == identifier.scheme.value,
                    WorkIdentifierRow.value == identifier.value,
                )
            )
            if found is None:
                self.session.add(
                    WorkIdentifierRow(
                        work_id=row.id,
                        scheme=identifier.scheme.value,
                        value=identifier.value,
                        version=identifier.version,
                        canonical_url=str(identifier.canonical_url)
                        if identifier.canonical_url
                        else None,
                        provider=identifier.provider,
                        raw_value=identifier.raw_value,
                    )
                )

        if work.version is not None:
            version_id = stable_id("work-version", f"{row.id}:{work.version.version_label}")
            version = self.session.get(WorkVersionRow, version_id)
            if version is None:
                self.session.add(
                    WorkVersionRow(
                        id=version_id,
                        work_id=row.id,
                        version_label=work.version.version_label,
                        version_date=work.version.version_date,
                        provider=work.version.provider,
                        raw_record=work.version.raw_record,
                    )
                )
        self.session.flush()
        return row

    def count(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(WorkRow)) or 0)


class ProblemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, problem: ProblemInstance) -> ProblemInstanceRow:
        row = self.session.get(ProblemInstanceRow, problem.id)
        if row is None:
            row = ProblemInstanceRow(
                id=problem.id,
                source_work_id=problem.source_work_id,
                task_family=problem.task_family.value,
                statement=problem.natural_language_statement,
                payload_json=problem.model_dump(mode="json"),
                extraction_method=problem.extraction_method.value,
                confidence=problem.confidence,
                review_status=problem.review_status.value,
            )
        else:
            row.source_work_id = problem.source_work_id
            row.task_family = problem.task_family.value
            row.statement = problem.natural_language_statement
            row.payload_json = problem.model_dump(mode="json")
            row.extraction_method = problem.extraction_method.value
            row.confidence = problem.confidence
            row.review_status = problem.review_status.value
        self.session.add(row)
        self.session.flush()
        return row

    def all(self) -> list[ProblemInstance]:
        stmt = select(ProblemInstanceRow).order_by(ProblemInstanceRow.id)
        rows = self.session.scalars(stmt).all()
        return [ProblemInstance.model_validate(row.payload_json) for row in rows]
