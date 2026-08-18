from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.corpus.schema import Asset, Work
from discovery.problems.schema import ProblemInstance
from discovery.storage.models import (
    AssetRow,
    AuthorRow,
    AuthorshipRow,
    CitationRow,
    MathematicalObjectRow,
    ProblemEvidenceRow,
    ProblemInstanceRow,
    ProblemMathRow,
    ProblemMethodRow,
    ProvenanceAssertionRow,
    ScientificMethodRow,
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
        existing: WorkRow | None = self.session.get(WorkRow, work.id)
        if existing is None:
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
                version = WorkVersionRow(
                    id=version_id,
                    work_id=row.id,
                    version_label=work.version.version_label,
                    version_date=work.version.version_date,
                    provider=work.version.provider,
                    raw_record=work.version.raw_record,
                )
            else:
                version.version_date = work.version.version_date
                version.provider = work.version.provider
                version.raw_record = work.version.raw_record
            self.session.add(version)

        self._upsert_authors(row.id, work)
        asset_repository = AssetRepository(self.session)
        for asset in work.assets:
            asset_repository.upsert(row.id, asset)
        self._upsert_provenance(row.id, work)

        self.session.flush()
        return row

    def _upsert_authors(self, work_id: str, work: Work) -> None:
        for position, author in enumerate(work.authors, start=1):
            row = self.session.get(AuthorRow, author.id)
            if row is None:
                row = AuthorRow(
                    id=author.id,
                    display_name=author.display_name,
                    identifiers_json=author.identifiers,
                )
            else:
                row.display_name = author.display_name
                row.identifiers_json = author.identifiers
            self.session.add(row)
            self.session.flush()

            authorship = self.session.scalar(
                select(AuthorshipRow).where(
                    AuthorshipRow.work_id == work_id,
                    AuthorshipRow.author_id == author.id,
                    AuthorshipRow.position == position,
                )
            )
            if authorship is None:
                authorship = AuthorshipRow(
                    work_id=work_id,
                    author_id=author.id,
                    position=position,
                    organization_ids=[],
                )
                self.session.add(authorship)

    def _upsert_provenance(self, work_id: str, work: Work) -> None:
        for index, provenance in enumerate(work.provenance):
            assertion_id = stable_id(
                "provenance-assertion",
                ":".join(
                    [
                        "work",
                        work_id,
                        provenance.provider,
                        provenance.source_identifier or "",
                        provenance.request_id or "",
                        str(index),
                    ]
                ),
            )
            row = self.session.get(ProvenanceAssertionRow, assertion_id)
            payload = provenance.model_dump(mode="json")
            if row is None:
                row = ProvenanceAssertionRow(
                    id=assertion_id,
                    subject_type="work",
                    subject_id=work_id,
                    predicate="retrieved_from",
                    value_json=payload,
                    provider=provenance.provider,
                    retrieved_at=provenance.retrieved_at,
                    evidence_json=payload,
                )
            else:
                row.value_json = payload
                row.provider = provenance.provider
                row.retrieved_at = provenance.retrieved_at
                row.evidence_json = payload
            self.session.add(row)

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
        self._replace_normalized_children(problem)
        self.session.flush()
        return row

    def _replace_normalized_children(self, problem: ProblemInstance) -> None:
        self.session.execute(
            delete(ProblemEvidenceRow).where(ProblemEvidenceRow.problem_id == problem.id)
        )
        self.session.execute(delete(ProblemMathRow).where(ProblemMathRow.problem_id == problem.id))
        self.session.execute(
            delete(ProblemMethodRow).where(ProblemMethodRow.problem_id == problem.id)
        )

        for index, evidence in enumerate(problem.evidence):
            self.session.add(
                ProblemEvidenceRow(
                    problem_id=problem.id,
                    evidence_index=index,
                    evidence_json=evidence.model_dump(mode="json"),
                )
            )

        for item in problem.mathematical_objects:
            object_id = stable_id(
                "mathematical-object",
                f"{item.object_type}:{item.name}:{item.representation or ''}",
            )
            object_row = self.session.get(MathematicalObjectRow, object_id)
            payload = item.model_dump(mode="json")
            if object_row is None:
                object_row = MathematicalObjectRow(
                    id=object_id,
                    name=item.name,
                    object_type=item.object_type,
                    canonical_form=item.representation,
                    payload_json=payload,
                )
            else:
                object_row.name = item.name
                object_row.object_type = item.object_type
                object_row.canonical_form = item.representation
                object_row.payload_json = payload
            self.session.add(object_row)
            self.session.flush()
            self.session.add(
                ProblemMathRow(
                    problem_id=problem.id,
                    math_object_id=object_id,
                    role=item.role or "unspecified",
                )
            )

        method_entries = [
            (method, method.role or "known_method") for method in problem.known_methods
        ]
        method_entries.extend(
            (method, method.role or "classical_baseline")
            for method in problem.classical_baselines
        )
        for method, role in method_entries:
            method_id = stable_id(
                "scientific-method",
                f"{method.method_type or 'unknown'}:{method.name}",
            )
            method_row = self.session.get(ScientificMethodRow, method_id)
            payload = method.model_dump(mode="json")
            if method_row is None:
                method_row = ScientificMethodRow(
                    id=method_id,
                    name=method.name,
                    method_type=method.method_type,
                    payload_json=payload,
                )
            else:
                method_row.name = method.name
                method_row.method_type = method.method_type
                method_row.payload_json = payload
            self.session.add(method_row)
            self.session.flush()
            self.session.add(
                ProblemMethodRow(
                    problem_id=problem.id,
                    method_id=method_id,
                    role=role,
                )
            )

    def all(self) -> list[ProblemInstance]:
        stmt = select(ProblemInstanceRow).order_by(ProblemInstanceRow.id)
        rows = self.session.scalars(stmt).all()
        return [ProblemInstance.model_validate(row.payload_json) for row in rows]


class CitationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_edge(
        self,
        *,
        source_work_id: str,
        target_work_id: str,
        provider: str,
        provider_edge_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CitationRow:
        row = self.session.scalar(
            select(CitationRow).where(
                CitationRow.source_work_id == source_work_id,
                CitationRow.target_work_id == target_work_id,
                CitationRow.provider == provider,
            )
        )
        if row is None:
            row = CitationRow(
                source_work_id=source_work_id,
                target_work_id=target_work_id,
                provider=provider,
                provider_edge_id=provider_edge_id,
                retrieved_at=datetime.now(UTC),
                metadata_json=metadata or {},
            )
        else:
            row.provider_edge_id = provider_edge_id or row.provider_edge_id
            row.retrieved_at = datetime.now(UTC)
            row.metadata_json = metadata or row.metadata_json
        self.session.add(row)
        self.session.flush()
        return row


class AssetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, work_id: str, asset: Asset) -> AssetRow:
        row = self.session.get(AssetRow, asset.id)
        rights_json = asset.rights.model_dump(mode="json") if asset.rights else {}
        if row is None:
            row = AssetRow(
                id=asset.id,
                work_id=work_id,
                provider=asset.provider,
                representation=asset.representation,
                url=str(asset.url) if asset.url else None,
                mime_type=asset.mime_type,
                availability=asset.availability,
                rights_json=rights_json,
                checksum=asset.checksum,
            )
        else:
            row.provider = asset.provider
            row.representation = asset.representation
            row.url = str(asset.url) if asset.url else None
            row.mime_type = asset.mime_type
            row.availability = asset.availability
            row.rights_json = rights_json
            row.checksum = asset.checksum
        self.session.add(row)
        self.session.flush()
        return row
