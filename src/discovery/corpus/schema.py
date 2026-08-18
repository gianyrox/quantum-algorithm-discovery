from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from discovery.core.ids import stable_id
from discovery.core.provenance import ProvenanceRecord, RightsStatement


class IdentifierScheme(StrEnum):
    DOI = "doi"
    PMID = "pmid"
    PMCID = "pmcid"
    ARXIV = "arxiv"
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    DATACITE = "datacite"
    DBLP = "dblp"
    ZBMATH = "zbmath"
    OTHER = "other"


class WorkIdentifier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme: IdentifierScheme
    value: str
    version: str | None = None
    canonical_url: HttpUrl | None = None
    provider: str | None = None
    raw_value: str | None = None


class WorkVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_label: str = "record"
    version_date: datetime | None = None
    provider: str | None = None
    raw_record: dict[str, object] = Field(default_factory=dict)


class Author(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    display_name: str
    identifiers: dict[str, str] = Field(default_factory=dict)


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    representation: str
    provider: str
    url: HttpUrl | None = None
    mime_type: str | None = None
    availability: str = "unknown"
    rights: RightsStatement | None = None
    checksum: str | None = None


class Work(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    abstract: str | None = None
    publication_year: int | None = None
    work_type: str | None = None
    primary_language: str | None = None
    identifiers: list[WorkIdentifier] = Field(default_factory=list)
    authors: list[Author] = Field(default_factory=list)
    assets: list[Asset] = Field(default_factory=list)
    version: WorkVersion | None = None
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    @classmethod
    def from_primary_identifier(
        cls,
        *,
        scheme: IdentifierScheme,
        value: str,
        title: str,
        abstract: str | None = None,
        publication_year: int | None = None,
        work_type: str | None = None,
        primary_language: str | None = None,
        authors: list[Author] | None = None,
        assets: list[Asset] | None = None,
        version: WorkVersion | None = None,
        provenance: list[ProvenanceRecord] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Work:
        return cls(
            id=stable_id("work", f"{scheme.value}:{value}"),
            title=title,
            abstract=abstract,
            publication_year=publication_year,
            work_type=work_type,
            primary_language=primary_language,
            identifiers=[WorkIdentifier(scheme=scheme, value=value)],
            authors=authors or [],
            assets=assets or [],
            version=version,
            provenance=provenance or [],
            metadata=metadata or {},
        )
