from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import ProvenanceRecord, RightsStatement, SoftwareIdentity
from discovery.corpus.schema import Asset

CANONICAL_FEED402_SPEC = "feed402/0.3"
KNOWN_FEED402_SPECS = ("feed402/0.1", "feed402/0.2", CANONICAL_FEED402_SPEC)


class Feed402ProtocolError(RuntimeError):
    pass


class Feed402RightsScope(BaseModel):
    model_config = ConfigDict(extra="allow")

    license: str | None = None
    license_url: str | None = None
    status: str | None = None
    tiers: list[str] = Field(default_factory=list)


class Feed402Rights(BaseModel):
    """Structured feed402 rights. Unknown or absent permissions grant nothing."""

    model_config = ConfigDict(extra="allow")

    metadata: Feed402RightsScope | None = None
    content: Feed402RightsScope | None = None
    redistribution: str = "unknown"
    tdm: str = "unknown"
    model_training: str = "unknown"
    retention: str = "unknown"
    citation_only: bool = False
    terms_url: str | None = None
    retrieved_at: datetime | None = None
    provider_release: str | None = None
    jurisdiction: str | None = None
    notes: str | None = None

    def permission(self, facet: str) -> str:
        value = getattr(self, facet, "unknown")
        if isinstance(value, str) and value in {"allowed", "denied", "unknown"}:
            if value != "unknown":
                return value
        if self.citation_only and facet in {"redistribution", "retention"}:
            return "denied"
        return "unknown"

    def permits(self, facet: str) -> bool:
        return self.permission(facet) == "allowed"

    def to_statement(self) -> RightsStatement:
        return RightsStatement(
            metadata_license=self.metadata.license if self.metadata is not None else None,
            content_license=self.content.license if self.content is not None else None,
            redistribution=self.permission("redistribution"),
            tdm=self.permission("tdm"),
            model_training=self.permission("model_training"),
            retention=self.permission("retention"),
            terms_url=self.terms_url,
            retrieved_at=self.retrieved_at,
        )


class Feed402Asset(BaseModel):
    model_config = ConfigDict(extra="allow")

    asset_id: str
    representation: str
    mime_type: str | None = None
    content_type: str | None = None
    canonical_url: str | None = None
    provider_url: str | None = None
    checksum: str | None = None
    size: int | None = Field(default=None, ge=0)
    version: str | None = None
    rights: Feed402Rights | None = None
    availability: str = "unknown"
    retrieved_at: datetime | None = None

    def to_asset(
        self,
        *,
        work_id: str,
        provider: str,
        inherited_rights: Feed402Rights | None = None,
    ) -> Asset:
        raw_url = self.canonical_url or self.provider_url
        effective_rights = self.rights or inherited_rights
        return Asset(
            id=self.asset_id
            or stable_id(
                "asset",
                f"{work_id}:{provider}:{raw_url}:{self.representation}",
            ),
            provider=provider,
            representation=self.representation,
            url=HttpUrl(raw_url) if raw_url is not None else None,
            mime_type=self.mime_type or self.content_type,
            availability=self.availability,
            rights=effective_rights.to_statement() if effective_rights is not None else None,
            checksum=self.checksum,
        )


class Feed402RetrievalProvenance(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    score: float
    rank: int = Field(ge=0)


class Feed402ExecutionProvenance(BaseModel):
    model_config = ConfigDict(extra="allow")

    level: int | None = Field(default=None, ge=0, le=3)
    request_id: str | None = None
    query_fingerprint: str | None = None
    query_plan_fingerprint: str | None = None
    provider_request_fingerprint: str | None = None
    corpus_sha256: str | None = None
    index_id: str | None = None
    index_build: str | None = None
    provider_release: str | None = None
    retrieval_pipeline: str | None = None
    software: str | None = None
    software_version: str | None = None
    git_commit: str | None = None
    response_sha256: str | None = None

    def to_provenance(self, *, provider: str, source_identifier: str | None) -> ProvenanceRecord:
        software: SoftwareIdentity | None = None
        if self.software:
            software = SoftwareIdentity(
                software=self.software,
                software_version=self.software_version,
                git_commit=self.git_commit,
            )
        return ProvenanceRecord(
            provider=provider,
            source_identifier=source_identifier,
            provider_release=self.provider_release,
            request_id=self.request_id,
            query_fingerprint=self.query_fingerprint,
            provider_request_fingerprint=self.provider_request_fingerprint,
            response_sha256=self.response_sha256,
            software=software,
        )


class Feed402Citation(BaseModel):
    """Canonical source/VDS citation shape with open-extension compatibility."""

    model_config = ConfigDict(extra="allow")

    type: str = "source"
    source_id: str | None = None
    provider: str | None = None
    retrieved_at: datetime | None = None
    license: str | None = None
    canonical_url: str | None = None
    rights: Feed402Rights | None = None
    assets: list[Feed402Asset] = Field(default_factory=list)
    result_index: list[int] = Field(default_factory=list)
    chunk_id: str | None = None
    retrieval: Feed402RetrievalProvenance | None = None
    execution: Feed402ExecutionProvenance | None = None

    def grounds_result(self, result_index: int, position: int) -> bool:
        if self.result_index:
            return result_index in self.result_index
        return position == result_index

    def provenance(self) -> ProvenanceRecord | None:
        if self.type != "source":
            return None
        provider = self.provider or "unknown"
        if self.execution is not None:
            record = self.execution.to_provenance(
                provider=provider,
                source_identifier=self.source_id,
            )
            if self.retrieved_at is not None:
                record = record.model_copy(update={"retrieved_at": self.retrieved_at})
            return record
        return ProvenanceRecord(
            provider=provider,
            source_identifier=self.source_id,
            retrieved_at=self.retrieved_at or datetime.now(UTC),
        )


class Feed402LineageEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    step: int = Field(ge=0)
    derived_object: str
    sources: list[int | str]
    transformation: str
    software: str | None = None
    software_version: str | None = None
    git_commit: str | None = None
    timestamp: datetime | None = None
    notes: str | None = None


class Feed402Receipt(BaseModel):
    model_config = ConfigDict(extra="allow")

    tier: str
    price_usd: float = Field(ge=0)
    tx: str
    paid_at: datetime


class Feed402Envelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: Any
    citation: list[Feed402Citation]
    lineage: list[Feed402LineageEntry] = Field(default_factory=list)
    receipt: Feed402Receipt | None = None
    raw: dict[str, object] = Field(default_factory=dict, exclude=True)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        require_citations: bool = True,
        require_receipt: bool = True,
    ) -> Feed402Envelope:
        normalized = dict(payload)
        citation_obj = normalized.get("citation")
        if citation_obj is None:
            citation_obj = normalized.get("citation_legacy")
        if isinstance(citation_obj, Mapping):
            normalized["citation"] = [dict(citation_obj)]
        elif isinstance(citation_obj, list):
            normalized["citation"] = citation_obj
        elif require_citations:
            raise Feed402ProtocolError("feed402 response is missing citation")
        else:
            normalized["citation"] = []

        if require_citations and not normalized["citation"]:
            raise Feed402ProtocolError("feed402 successful response has no citations")
        if "data" not in normalized:
            raise Feed402ProtocolError("feed402 response is missing data")
        if require_receipt and "receipt" not in normalized:
            raise Feed402ProtocolError("feed402 response is missing receipt")

        envelope = cls.model_validate(normalized)
        return envelope.model_copy(update={"raw": dict(payload)})

    def citation_for_result(self, result_index: int) -> Feed402Citation | None:
        for position, citation in enumerate(self.citation):
            if citation.grounds_result(result_index, position):
                return citation
        return None

    @property
    def source_citations(self) -> list[Feed402Citation]:
        return [citation for citation in self.citation if citation.type == "source"]


class RecordedFeed402Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    envelope: Feed402Envelope

    @property
    def citation_count(self) -> int:
        return len(self.envelope.citation)

    @property
    def lineage_count(self) -> int:
        return len(self.envelope.lineage)


def parse_optional_feed402_envelope(payload: Mapping[str, Any]) -> Feed402Envelope | None:
    if "data" not in payload:
        return None
    if "citation" not in payload and "citation_legacy" not in payload:
        return None
    return Feed402Envelope.from_mapping(payload, require_receipt=False)
