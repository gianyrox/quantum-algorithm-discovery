from __future__ import annotations

import re
from dataclasses import dataclass

from discovery.corpus.schema import IdentifierScheme, Work, WorkIdentifier


def normalize_identifier(identifier: WorkIdentifier) -> tuple[str, str]:
    value = identifier.value.strip()
    if identifier.scheme == IdentifierScheme.DOI:
        value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
        value = value.casefold()
    elif identifier.scheme in {IdentifierScheme.PMID, IdentifierScheme.PMCID}:
        value = value.upper() if identifier.scheme == IdentifierScheme.PMCID else value
    elif identifier.scheme == IdentifierScheme.ARXIV:
        value = re.sub(r"^arxiv:", "", value, flags=re.IGNORECASE)
    return identifier.scheme.value, value


@dataclass(frozen=True)
class IdentityEvidence:
    relation: str
    reason: str
    confidence: float


def exact_identity_evidence(left: Work, right: Work) -> IdentityEvidence | None:
    left_ids = {normalize_identifier(item) for item in left.identifiers}
    right_ids = {normalize_identifier(item) for item in right.identifiers}
    common = left_ids & right_ids
    if common:
        scheme, value = sorted(common)[0]
        return IdentityEvidence(
            relation="same_work",
            reason=f"exact identifier agreement on {scheme}:{value}",
            confidence=1.0,
        )
    return None


def possible_identity_evidence(left: Work, right: Work) -> IdentityEvidence | None:
    left_title = re.sub(r"\W+", " ", left.title.casefold()).strip()
    right_title = re.sub(r"\W+", " ", right.title.casefold()).strip()
    if not left_title or not right_title:
        return None
    left_tokens = set(left_title.split())
    right_tokens = set(right_title.split())
    union = left_tokens | right_tokens
    score = len(left_tokens & right_tokens) / len(union) if union else 0.0
    if (
        left.publication_year
        and right.publication_year
        and abs(left.publication_year - right.publication_year) > 1
    ):
        score *= 0.5
    if score < 0.82:
        return None
    return IdentityEvidence(
        relation="possible_same_work",
        reason="title/year similarity; never auto-promoted to same_work",
        confidence=round(score, 6),
    )
