from __future__ import annotations

from typing import Protocol

from discovery.documents.schema import ParsedDocument


class DocumentParser(Protocol):
    name: str
    version: str
    supported_formats: set[str]

    def parse(self, *, work_id: str, asset_id: str, content: bytes) -> ParsedDocument: ...


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, DocumentParser] = {}

    def register(self, parser: DocumentParser) -> None:
        for source_format in parser.supported_formats:
            self._parsers[source_format.casefold()] = parser

    def get(self, source_format: str) -> DocumentParser:
        key = source_format.casefold()
        if key not in self._parsers:
            raise KeyError(f"no parser registered for {source_format}")
        return self._parsers[key]
