from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.corpus.schema import IdentifierScheme
from discovery.retrieval.gateway_models import IdentityResolution
from discovery.storage.models import IdentityAssertionRow, WorkIdentifierRow


class IdentityResolutionIngestReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assertions_persisted: int = 0
    exact_aliases_attached: int = 0
    conflicts: list[str] = Field(default_factory=list)


def parse_identifier(value: str) -> tuple[str, str] | None:
    raw = value.strip()
    lowered = raw.casefold()
    if lowered.startswith("https://doi.org/") or lowered.startswith("http://doi.org/"):
        return IdentifierScheme.DOI.value, urlparse(raw).path.lstrip("/").casefold()
    if lowered.startswith("doi:"):
        return IdentifierScheme.DOI.value, raw.split(":", 1)[1].casefold()
    if lowered.startswith("pmid:"):
        return IdentifierScheme.PMID.value, raw.split(":", 1)[1]
    if lowered.startswith("pmcid:"):
        return IdentifierScheme.PMCID.value, raw.split(":", 1)[1].upper()
    if raw.upper().startswith("PMC") and raw[3:].isdigit():
        return IdentifierScheme.PMCID.value, raw.upper()
    if lowered.startswith("arxiv:"):
        return IdentifierScheme.ARXIV.value, raw.split(":", 1)[1]
    if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", raw):
        return IdentifierScheme.ARXIV.value, raw
    if "openalex.org/" in lowered:
        return IdentifierScheme.OPENALEX.value, urlparse(raw).path.rstrip("/").rsplit("/", 1)[-1]
    if lowered.startswith("openalex:"):
        return IdentifierScheme.OPENALEX.value, raw.split(":", 1)[1]
    if raw.startswith("W") and raw[1:].isdigit():
        return IdentifierScheme.OPENALEX.value, raw
    if raw.casefold().startswith("10.") and "/" in raw:
        return IdentifierScheme.DOI.value, raw.casefold()
    return None


class IdentityGraphService:
    """Persist provider assertions and conservatively attach exact identifier aliases.

    Only provider-asserted `same_work` edges are eligible for automatic alias
    attachment. `possible_same_work`, title similarity, and other fuzzy evidence
    are never promoted into identity.
    """

    _EXACT_RELATIONS = {"same_work", "same_as"}

    def __init__(self, session: Session) -> None:
        self.session = session

    def ingest(self, resolution: IdentityResolution) -> IdentityResolutionIngestReport:
        persisted = 0
        aliases = 0
        conflicts: list[str] = []
        now = datetime.now(UTC)
        for assertion in resolution.assertions:
            assertion_id = stable_id(
                "identity-assertion",
                ":".join(
                    [
                        assertion.source_identifier,
                        assertion.relation_type,
                        assertion.target_identifier,
                        assertion.provider,
                    ]
                ),
            )
            row = self.session.get(IdentityAssertionRow, assertion_id)
            if row is None:
                row = IdentityAssertionRow(
                    id=assertion_id,
                    source_identifier=assertion.source_identifier,
                    relation_type=assertion.relation_type,
                    target_identifier=assertion.target_identifier,
                    provider=assertion.provider,
                    confidence=assertion.confidence,
                    retrieved_at=now,
                    payload_json=assertion.payload,
                )
            else:
                row.confidence = assertion.confidence
                row.retrieved_at = now
                row.payload_json = assertion.payload
            self.session.add(row)
            persisted += 1
            if assertion.relation_type in self._EXACT_RELATIONS:
                attached, conflict = self._attach_exact_alias(
                    assertion.source_identifier,
                    assertion.target_identifier,
                    assertion.provider,
                )
                aliases += attached
                if conflict:
                    conflicts.append(conflict)
        self.session.flush()
        return IdentityResolutionIngestReport(
            assertions_persisted=persisted,
            exact_aliases_attached=aliases,
            conflicts=conflicts,
        )

    def _work_id(self, value: str) -> str | None:
        parsed = parse_identifier(value)
        if parsed is None:
            return None
        scheme, normalized = parsed
        row = self.session.scalar(
            select(WorkIdentifierRow).where(
                WorkIdentifierRow.scheme == scheme,
                WorkIdentifierRow.value == normalized,
            )
        )
        return row.work_id if row is not None else None

    def _attach_exact_alias(
        self,
        source: str,
        target: str,
        provider: str,
    ) -> tuple[int, str | None]:
        source_work = self._work_id(source)
        target_work = self._work_id(target)
        if source_work and target_work:
            if source_work != target_work:
                return 0, f"exact-identity-conflict:{source_work}:{target_work}:{source}:{target}"
            return 0, None
        known_work = source_work or target_work
        unknown_identifier = target if source_work else source if target_work else None
        if known_work is None or unknown_identifier is None:
            return 0, None
        parsed = parse_identifier(unknown_identifier)
        if parsed is None:
            return 0, None
        scheme, value = parsed
        existing = self.session.scalar(
            select(WorkIdentifierRow).where(
                WorkIdentifierRow.scheme == scheme,
                WorkIdentifierRow.value == value,
            )
        )
        if existing is not None:
            if existing.work_id != known_work:
                return 0, f"identifier-already-owned:{scheme}:{value}:{existing.work_id}"
            return 0, None
        self.session.add(
            WorkIdentifierRow(
                work_id=known_work,
                scheme=scheme,
                value=value,
                provider=provider,
                raw_value=unknown_identifier,
            )
        )
        self.session.flush()
        return 1, None
