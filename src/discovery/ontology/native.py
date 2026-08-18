from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.storage.models import (
    ConceptRelationRow,
    ConceptRow,
    SourceReleaseRow,
    SourceRow,
    TermRow,
)


class NativeVocabularyRecord(BaseModel):
    """Loss-minimizing normalized view of one source vocabulary concept."""

    model_config = ConfigDict(extra="forbid")

    native_id: str
    preferred_label: str
    alternate_labels: list[str] = Field(default_factory=list)
    historical_labels: list[str] = Field(default_factory=list)
    broader_ids: list[str] = Field(default_factory=list)
    narrower_ids: list[str] = Field(default_factory=list)
    related_ids: list[str] = Field(default_factory=list)
    definition: str | None = None
    deprecated: bool = False
    replaced_by_ids: list[str] = Field(default_factory=list)
    native_payload: dict[str, object] = Field(default_factory=dict)


class NativeVocabularyImportReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    release: str
    concepts_added: int = 0
    terms_added: int = 0
    relations_added: int = 0


def _native_concept_id(source_id: str, release: str, native_id: str) -> str:
    return stable_id("native-concept", f"{source_id}:{release}:{native_id}")


class NativeVocabularyImporter:
    """Import native assertions without coercing them into stronger semantics.

    `broader` stays `broader`; it is never silently promoted to `subClassOf`.
    Release identity is preserved through the source-release registry and in
    concept origin metadata.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def import_records(
        self,
        records: list[NativeVocabularyRecord],
        *,
        source_id: str,
        source_name: str,
        release: str,
        source_type: str = "native_vocabulary",
    ) -> NativeVocabularyImportReport:
        self._ensure_source(source_id, source_name, source_type, release)
        report = NativeVocabularyImportReport(source_id=source_id, release=release)

        for record in records:
            concept_id = _native_concept_id(source_id, release, record.native_id)
            row = self.session.get(ConceptRow, concept_id)
            if row is None:
                row = ConceptRow(
                    id=concept_id,
                    discipline_id=None,
                    canonical_concept=record.preferred_label,
                    concept_type="native_concept",
                    short_definition=record.definition,
                    origin=f"{source_id}:{release}",
                    status="deprecated" if record.deprecated else "native",
                    confidence="source_asserted",
                )
                self.session.add(row)
                report.concepts_added += 1
            else:
                row.canonical_concept = record.preferred_label
                row.short_definition = record.definition
                row.status = "deprecated" if record.deprecated else "native"
                row.confidence = "source_asserted"
                self.session.add(row)

            report.terms_added += self._upsert_term(
                concept_id,
                record.preferred_label,
                "preferred",
                f"native_id={record.native_id};release={release}",
            )
            for label in record.alternate_labels:
                report.terms_added += self._upsert_term(
                    concept_id, label, "synonym", f"release={release}"
                )
            for label in record.historical_labels:
                report.terms_added += self._upsert_term(
                    concept_id, label, "historical", f"release={release}"
                )

        self.session.flush()
        by_native = {
            record.native_id: _native_concept_id(source_id, release, record.native_id)
            for record in records
        }
        for record in records:
            source_concept_id = by_native[record.native_id]
            for relationship, targets in (
                ("broader", record.broader_ids),
                ("narrower", record.narrower_ids),
                ("related", record.related_ids),
                ("superseded_by", record.replaced_by_ids),
            ):
                for target_native_id in targets:
                    target_concept_id = by_native.get(target_native_id)
                    if target_concept_id is None:
                        target_concept_id = _native_concept_id(
                            source_id, release, target_native_id
                        )
                    report.relations_added += self._upsert_relation(
                        source_concept_id,
                        relationship,
                        target_concept_id,
                    )
        self.session.flush()
        return report

    def _ensure_source(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        release: str,
    ) -> None:
        source = self.session.get(SourceRow, source_id)
        if source is None:
            source = SourceRow(
                id=source_id,
                name=source_name,
                source_type=source_type,
                status="native",
                metadata_json={"normalization": "additive"},
            )
            self.session.add(source)
            self.session.flush()
        release_row = self.session.scalar(
            select(SourceReleaseRow).where(
                SourceReleaseRow.source_id == source_id,
                SourceReleaseRow.release == release,
            )
        )
        if release_row is None:
            self.session.add(
                SourceReleaseRow(
                    source_id=source_id,
                    release=release,
                    metadata_json={"imported": True},
                )
            )
            self.session.flush()

    def _upsert_term(
        self,
        concept_id: str,
        term: str,
        term_type: str,
        context: str,
    ) -> int:
        existing = self.session.scalar(
            select(TermRow).where(
                TermRow.concept_id == concept_id,
                TermRow.term == term,
                TermRow.term_type == term_type,
                TermRow.context == context,
            )
        )
        if existing is not None:
            return 0
        self.session.add(
            TermRow(
                concept_id=concept_id,
                term=term,
                term_type=term_type,
                context=context,
            )
        )
        return 1

    def _upsert_relation(self, source_id: str, relationship: str, target_id: str) -> int:
        existing = self.session.scalar(
            select(ConceptRelationRow).where(
                ConceptRelationRow.source_concept_id == source_id,
                ConceptRelationRow.relationship == relationship,
                ConceptRelationRow.target_concept_id == target_id,
            )
        )
        if existing is not None:
            return 0
        self.session.add(
            ConceptRelationRow(
                source_concept_id=source_id,
                relationship=relationship,
                target_concept_id=target_id,
            )
        )
        return 1


def parse_native_jsonl(path: Path) -> list[NativeVocabularyRecord]:
    records: list[NativeVocabularyRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(NativeVocabularyRecord.model_validate(json.loads(line)))
    return records


def parse_obo(path: Path) -> list[NativeVocabularyRecord]:
    records: list[NativeVocabularyRecord] = []
    current: dict[str, list[str]] = {}

    def first_value(key: str) -> str | None:
        values = current.get(key)
        return values[0] if values else None

    def finish() -> None:
        native_id = first_value("id")
        name = first_value("name")
        if native_id is None or name is None:
            current.clear()
            return
        synonyms = []
        for value in current.get("synonym", []):
            match = re.match(r'"(.*?)"', value)
            if match:
                synonyms.append(match.group(1))
        broader = [value.split(" ! ", 1)[0].strip() for value in current.get("is_a", [])]
        replaced = [value.strip() for value in current.get("replaced_by", [])]
        records.append(
            NativeVocabularyRecord(
                native_id=native_id,
                preferred_label=name,
                alternate_labels=synonyms,
                broader_ids=broader,
                definition=first_value("def"),
                deprecated=(current.get("is_obsolete") or ["false"])[0].casefold()
                == "true",
                replaced_by_ids=replaced,
                native_payload={key: list(values) for key, values in current.items()},
            )
        )
        current.clear()

    in_term = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "[Term]":
            if in_term:
                finish()
            in_term = True
            continue
        if line.startswith("[") and line.endswith("]"):
            if in_term:
                finish()
            in_term = False
            continue
        if not in_term or not line or line.startswith("!") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        current.setdefault(key.strip(), []).append(value.strip())
    if in_term:
        finish()
    return records


def parse_skos_rdfxml(path: Path) -> list[NativeVocabularyRecord]:
    namespaces = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
    }
    root = ET.parse(path).getroot()
    records: list[NativeVocabularyRecord] = []
    for concept in root.findall(".//skos:Concept", namespaces):
        native_id = concept.attrib.get(f"{{{namespaces['rdf']}}}about")
        preferred = concept.find("skos:prefLabel", namespaces)
        if native_id is None or preferred is None or preferred.text is None:
            continue
        alternate = [
            item.text.strip()
            for item in concept.findall("skos:altLabel", namespaces)
            if item.text and item.text.strip()
        ]
        broader = [
            item.attrib[f"{{{namespaces['rdf']}}}resource"]
            for item in concept.findall("skos:broader", namespaces)
            if f"{{{namespaces['rdf']}}}resource" in item.attrib
        ]
        narrower = [
            item.attrib[f"{{{namespaces['rdf']}}}resource"]
            for item in concept.findall("skos:narrower", namespaces)
            if f"{{{namespaces['rdf']}}}resource" in item.attrib
        ]
        related = [
            item.attrib[f"{{{namespaces['rdf']}}}resource"]
            for item in concept.findall("skos:related", namespaces)
            if f"{{{namespaces['rdf']}}}resource" in item.attrib
        ]
        definition = concept.find("skos:definition", namespaces)
        records.append(
            NativeVocabularyRecord(
                native_id=native_id,
                preferred_label=preferred.text.strip(),
                alternate_labels=alternate,
                broader_ids=broader,
                narrower_ids=narrower,
                related_ids=related,
                definition=definition.text.strip()
                if definition is not None and definition.text
                else None,
            )
        )
    return records
