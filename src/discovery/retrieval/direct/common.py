from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from discovery.core.ids import stable_id
from discovery.corpus.schema import Author, IdentifierScheme, WorkIdentifier

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def clean_markup(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _SPACE.sub(" ", _TAG.sub(" ", value)).strip()
    return cleaned or None


def normalize_doi(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.casefold().startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return normalized.casefold() or None


def normalize_openalex_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().rstrip("/")
    if "/" in normalized:
        normalized = normalized.rsplit("/", 1)[-1]
    return normalized or None


def identifier(
    scheme: IdentifierScheme,
    value: str | None,
    *,
    provider: str,
) -> WorkIdentifier | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    if scheme == IdentifierScheme.DOI:
        doi = normalize_doi(normalized)
        if doi is None:
            return None
        normalized = doi
    if scheme == IdentifierScheme.OPENALEX:
        openalex = normalize_openalex_id(normalized)
        if openalex is None:
            return None
        normalized = openalex
    return WorkIdentifier(
        scheme=scheme,
        value=normalized,
        provider=provider,
        raw_value=value,
    )


def stable_author(provider: str, display_name: str, provider_id: str | None = None) -> Author:
    author_id = provider_id or stable_id("author", f"{provider}:{display_name.casefold()}")
    return Author(id=author_id, display_name=display_name)


def as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
