from __future__ import annotations

from typing import Protocol

from discovery.documents.schema import ParsedDocument
from discovery.problems.schema import ProblemInstance


class ProblemExtractor(Protocol):
    name: str
    version: str

    def extract(self, document: ParsedDocument) -> list[ProblemInstance]: ...


class ExtractionNotConfigured(RuntimeError):
    pass
