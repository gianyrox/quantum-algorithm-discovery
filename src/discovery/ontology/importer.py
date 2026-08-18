from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.ontology.models import OntologyImportReport
from discovery.storage.models import (
    ConceptRelationRow,
    ConceptRow,
    DisciplineRow,
    ModelMethodRow,
    SourceRow,
    TermRow,
)


class OntologySeedImporter:
    """Idempotent importer for the v0.1 retrieval scaffold.

    Imported records are explicitly marked as seed/scaffold rather than
    authoritative native vocabulary assertions.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def import_directory(self, path: Path) -> OntologyImportReport:
        report = OntologyImportReport()
        self._ensure_source()
        report.disciplines = self._disciplines(path / "DISCIPLINES.csv")
        report.concepts = self._concepts(path / "CONCEPTS.csv")
        report.terms = self._terms(path / "TERMS.csv")
        report.relationships = self._relationships(path / "RELATIONSHIPS.csv")
        report.models_equations_methods = self._models(path / "MODELS_EQUATIONS_METHODS.csv")
        return report

    def _ensure_source(self) -> None:
        if self.session.get(SourceRow, "ontology_v0_1") is None:
            self.session.add(
                SourceRow(
                    id="ontology_v0_1",
                    name="Scientific Retrieval Ontology v0.1",
                    source_type="retrieval_scaffold",
                    status="seed",
                    metadata_json={
                        "authority": "scaffold",
                        "note": "Broad retrieval seed; native sources supersede/enrich it.",
                    },
                )
            )

    @staticmethod
    def _rows(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))

    def _disciplines(self, path: Path) -> int:
        count = 0
        for raw in self._rows(path):
            row = self.session.get(DisciplineRow, raw["discipline_id"])
            if row is None:
                self.session.add(
                    DisciplineRow(
                        id=raw["discipline_id"],
                        name=raw["name"],
                        parent_id=raw["parent_id"] or None,
                        level=int(raw["level"] or 0),
                        description=raw["description"] or None,
                        source_id="ontology_v0_1",
                    )
                )
                count += 1
        self.session.flush()
        return count

    def _concepts(self, path: Path) -> int:
        count = 0
        for raw in self._rows(path):
            if self.session.get(ConceptRow, raw["concept_id"]) is None:
                self.session.add(
                    ConceptRow(
                        id=raw["concept_id"],
                        discipline_id=raw["discipline_id"] or None,
                        canonical_concept=raw["canonical_concept"],
                        concept_type=raw["concept_type"] or "other",
                        short_definition=raw["short_definition"] or None,
                        origin="ontology_v0_1",
                        status="seed",
                        confidence="scaffold",
                    )
                )
                count += 1
        self.session.flush()
        return count

    def _terms(self, path: Path) -> int:
        count = 0
        for raw in self._rows(path):
            context = raw["context"] or ""
            found = self.session.scalar(
                select(TermRow).where(
                    TermRow.concept_id == raw["concept_id"],
                    TermRow.term == raw["term"],
                    TermRow.term_type == raw["term_type"],
                    TermRow.context == context,
                )
            )
            if found is None:
                self.session.add(
                    TermRow(
                        concept_id=raw["concept_id"],
                        term=raw["term"],
                        term_type=raw["term_type"],
                        context=context,
                    )
                )
                count += 1
        self.session.flush()
        return count

    def _relationships(self, path: Path) -> int:
        count = 0
        for raw in self._rows(path):
            found = self.session.scalar(
                select(ConceptRelationRow).where(
                    ConceptRelationRow.source_concept_id == raw["source_concept_id"],
                    ConceptRelationRow.relationship == raw["relationship"],
                    ConceptRelationRow.target_concept_id == raw["target_concept_id"],
                )
            )
            if found is None:
                self.session.add(
                    ConceptRelationRow(
                        source_concept_id=raw["source_concept_id"],
                        relationship=raw["relationship"],
                        target_concept_id=raw["target_concept_id"],
                    )
                )
                count += 1
        self.session.flush()
        return count

    def _models(self, path: Path) -> int:
        count = 0
        for raw in self._rows(path):
            existing = self.session.scalar(
                select(ModelMethodRow).where(
                    ModelMethodRow.concept_id == (raw["concept_id"] or None),
                    ModelMethodRow.name == raw["name"],
                    ModelMethodRow.object_type == raw["type"],
                )
            )
            if existing is None:
                related = [
                    item.strip()
                    for item in raw["related_concepts"].split(";")
                    if item.strip()
                ]
                self.session.add(
                    ModelMethodRow(
                        concept_id=raw["concept_id"] or None,
                        name=raw["name"],
                        object_type=raw["type"],
                        discipline=raw["discipline"] or None,
                        related_concepts=related,
                    )
                )
                count += 1
        self.session.flush()
        return count
