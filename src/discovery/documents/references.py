from __future__ import annotations

import re

from discovery.core.ids import stable_id
from discovery.documents.schema import ReferenceOccurrence

_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)
_PMID_RE = re.compile(r"\bPMID\s*[:#]?\s*(\d{6,9})\b", re.IGNORECASE)
_ARXIV_RE = re.compile(r"\barXiv\s*:\s*([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)\b", re.IGNORECASE)


def infer_reference_identifiers(raw_text: str) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    doi = _DOI_RE.search(raw_text)
    if doi:
        identifiers["doi"] = doi.group(0).rstrip(".,;)").casefold()
    pmid = _PMID_RE.search(raw_text)
    if pmid:
        identifiers["pmid"] = pmid.group(1)
    arxiv = _ARXIV_RE.search(raw_text)
    if arxiv:
        identifiers["arxiv"] = arxiv.group(1)
    return identifiers


def reference_from_text(work_id: str, index: int, raw_text: str) -> ReferenceOccurrence:
    return ReferenceOccurrence(
        id=stable_id("reference", f"{work_id}:{index}:{raw_text}"),
        order=index,
        raw_text=raw_text.strip(),
        identifiers=infer_reference_identifiers(raw_text),
    )
