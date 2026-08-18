from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from discovery.core.ids import stable_id
from discovery.documents.references import infer_reference_identifiers
from discovery.documents.schema import (
    DocumentSection,
    EquationOccurrence,
    FigureOccurrence,
    ParsedDocument,
    ReferenceOccurrence,
    TableOccurrence,
)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


class PlainTextParser:
    name = "plain-text"
    version = "0.10"
    supported_formats = {"text", "txt", "text/plain", "plain"}

    def parse(self, *, work_id: str, asset_id: str, content: bytes) -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        return ParsedDocument(
            work_id=work_id,
            asset_id=asset_id,
            source_format="text/plain",
            parser=self.name,
            parser_version=self.version,
            sections=[
                DocumentSection(
                    id=stable_id("section", f"{work_id}:{asset_id}:0"),
                    order=0,
                    section_type="body",
                    text=text.strip(),
                )
            ],
        )


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self._heading_level: int | None = None
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "div", "section", "br", "li"}:
            self.parts.append("\n")
        if len(tag) == 2 and tag.startswith("h") and tag[1].isdigit():
            self._heading_level = int(tag[1])
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._heading_level is not None and tag == f"h{self._heading_level}":
            title = _clean_text("".join(self._heading_parts))
            if title:
                self.headings.append((self._heading_level, title))
            self._heading_level = None
            self._heading_parts = []
        if tag in {"p", "div", "section", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)
        if self._heading_level is not None:
            self._heading_parts.append(data)


class SimpleHTMLDocumentParser:
    name = "stdlib-html"
    version = "0.10"
    supported_formats = {"html", "text/html"}

    def parse(self, *, work_id: str, asset_id: str, content: bytes) -> ParsedDocument:
        parser = _TextHTMLParser()
        parser.feed(content.decode("utf-8", errors="replace"))
        text = re.sub(r"\n\s*\n+", "\n\n", "".join(parser.parts)).strip()
        sections = [
            DocumentSection(
                id=stable_id("section", f"{work_id}:{asset_id}:html:0"),
                title=parser.headings[0][1] if parser.headings else None,
                section_type="body",
                order=0,
                text=text,
            )
        ]
        return ParsedDocument(
            work_id=work_id,
            asset_id=asset_id,
            source_format="text/html",
            parser=self.name,
            parser_version=self.version,
            sections=sections,
            warnings=["HTML structure is conservatively flattened by the stdlib parser."],
        )


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _element_text(element: ET.Element) -> str:
    return _clean_text(" ".join(part for part in element.itertext()))


class JATSParser:
    name = "stdlib-jats"
    version = "0.10"
    supported_formats = {"jats", "xml", "application/xml", "application/jats+xml"}

    def parse(self, *, work_id: str, asset_id: str, content: bytes) -> ParsedDocument:
        root = ET.fromstring(content)
        sections: list[DocumentSection] = []
        equations: list[EquationOccurrence] = []
        figures: list[FigureOccurrence] = []
        tables: list[TableOccurrence] = []
        references: list[ReferenceOccurrence] = []

        section_index = 0
        for element in root.iter():
            name = _local_name(element.tag)
            if name == "sec":
                title_element = next(
                    (child for child in element if _local_name(child.tag) == "title"), None
                )
                title = _element_text(title_element) if title_element is not None else None
                paragraphs = [
                    _element_text(child)
                    for child in element
                    if _local_name(child.tag) in {"p", "statement", "disp-quote"}
                ]
                body = "\n\n".join(item for item in paragraphs if item)
                if body or title:
                    sections.append(
                        DocumentSection(
                            id=stable_id(
                                "section", f"{work_id}:{asset_id}:jats:{section_index}"
                            ),
                            title=title,
                            section_type="sec",
                            order=section_index,
                            text=body,
                        )
                    )
                    section_index += 1
            elif name in {"disp-formula", "inline-formula"}:
                mathml_element = next(
                    (child for child in element.iter() if _local_name(child.tag) == "math"), None
                )
                tex_element = next(
                    (
                        child
                        for child in element.iter()
                        if _local_name(child.tag) in {"tex-math", "alternatives"}
                    ),
                    None,
                )
                equations.append(
                    EquationOccurrence(
                        id=stable_id(
                            "equation", f"{work_id}:{asset_id}:jats:{len(equations)}"
                        ),
                        label=element.attrib.get("id"),
                        latex=_element_text(tex_element) if tex_element is not None else None,
                        mathml=ET.tostring(mathml_element, encoding="unicode")
                        if mathml_element is not None
                        else None,
                    )
                )
            elif name == "fig":
                caption = next(
                    (child for child in element.iter() if _local_name(child.tag) == "caption"),
                    None,
                )
                figures.append(
                    FigureOccurrence(
                        id=stable_id("figure", f"{work_id}:{asset_id}:{len(figures)}"),
                        label=element.attrib.get("id"),
                        caption=_element_text(caption) if caption is not None else None,
                    )
                )
            elif name == "table-wrap":
                caption = next(
                    (child for child in element.iter() if _local_name(child.tag) == "caption"),
                    None,
                )
                tables.append(
                    TableOccurrence(
                        id=stable_id("table", f"{work_id}:{asset_id}:{len(tables)}"),
                        label=element.attrib.get("id"),
                        caption=_element_text(caption) if caption is not None else None,
                    )
                )
            elif name == "ref":
                raw_reference = _element_text(element)
                if raw_reference:
                    references.append(
                        ReferenceOccurrence(
                            id=stable_id(
                                "reference",
                                f"{work_id}:{asset_id}:jats:{len(references)}:{raw_reference}",
                            ),
                            order=len(references),
                            raw_text=raw_reference,
                            identifiers=infer_reference_identifiers(raw_reference),
                        )
                    )

        if not sections:
            body_text = _element_text(root)
            sections.append(
                DocumentSection(
                    id=stable_id("section", f"{work_id}:{asset_id}:jats:0"),
                    order=0,
                    section_type="body",
                    text=body_text,
                )
            )
        return ParsedDocument(
            work_id=work_id,
            asset_id=asset_id,
            source_format="jats",
            parser=self.name,
            parser_version=self.version,
            sections=sections,
            equations=equations,
            figures=figures,
            tables=tables,
            references=references,
        )


class TEIParser:
    name = "stdlib-tei"
    version = "0.10"
    supported_formats = {"tei", "application/tei+xml"}

    def parse(self, *, work_id: str, asset_id: str, content: bytes) -> ParsedDocument:
        root = ET.fromstring(content)
        divisions = [element for element in root.iter() if _local_name(element.tag) == "div"]
        sections: list[DocumentSection] = []
        for index, division in enumerate(divisions):
            head = next(
                (child for child in division if _local_name(child.tag) == "head"), None
            )
            paragraphs = [
                _element_text(child)
                for child in division
                if _local_name(child.tag) in {"p", "ab"}
            ]
            sections.append(
                DocumentSection(
                    id=stable_id("section", f"{work_id}:{asset_id}:tei:{index}"),
                    title=_element_text(head) if head is not None else None,
                    section_type="div",
                    order=index,
                    text="\n\n".join(item for item in paragraphs if item),
                )
            )
        if not sections:
            sections.append(
                DocumentSection(
                    id=stable_id("section", f"{work_id}:{asset_id}:tei:0"),
                    order=0,
                    section_type="body",
                    text=_element_text(root),
                )
            )
        references: list[ReferenceOccurrence] = []
        for element in root.iter():
            if _local_name(element.tag) not in {"bibl", "biblStruct"}:
                continue
            raw_reference = _element_text(element)
            if not raw_reference:
                continue
            references.append(
                ReferenceOccurrence(
                    id=stable_id(
                        "reference",
                        f"{work_id}:{asset_id}:tei:{len(references)}:{raw_reference}",
                    ),
                    order=len(references),
                    raw_text=raw_reference,
                    identifiers=infer_reference_identifiers(raw_reference),
                )
            )
        return ParsedDocument(
            work_id=work_id,
            asset_id=asset_id,
            source_format="tei",
            parser=self.name,
            parser_version=self.version,
            sections=sections,
            references=references,
        )


_SECTION_RE = re.compile(r"\\(?P<kind>section|subsection|subsubsection)\*?\{(?P<title>[^}]*)\}")
_EQUATION_RE = re.compile(
    r"\\begin\{(?P<env>equation\*?|align\*?|gather\*?)\}(?P<body>.*?)\\end\{(?P=env)\}",
    re.DOTALL,
)
_DISPLAY_MATH_RE = re.compile(r"\\\[(?P<body>.*?)\\\]", re.DOTALL)
_BIBITEM_RE = re.compile(
    r"\\bibitem(?:\[[^]]*\])?\{[^}]+\}(?P<body>.*?)(?=\\bibitem|\\end\{thebibliography\}|$)",
    re.DOTALL,
)


class LatexParser:
    name = "stdlib-latex"
    version = "0.10"
    supported_formats = {"tex", "latex", "application/x-tex", "text/x-tex"}

    def parse(self, *, work_id: str, asset_id: str, content: bytes) -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        section_matches = list(_SECTION_RE.finditer(text))
        sections: list[DocumentSection] = []
        if section_matches:
            for index, match in enumerate(section_matches):
                start = match.end()
                end = (
                    section_matches[index + 1].start()
                    if index + 1 < len(section_matches)
                    else len(text)
                )
                sections.append(
                    DocumentSection(
                        id=stable_id("section", f"{work_id}:{asset_id}:tex:{index}"),
                        title=_clean_text(match.group("title")),
                        section_type=match.group("kind"),
                        order=index,
                        text=text[start:end].strip(),
                    )
                )
        else:
            sections.append(
                DocumentSection(
                    id=stable_id("section", f"{work_id}:{asset_id}:tex:0"),
                    order=0,
                    section_type="body",
                    text=text.strip(),
                )
            )
        equations: list[EquationOccurrence] = []
        for match in list(_EQUATION_RE.finditer(text)) + list(_DISPLAY_MATH_RE.finditer(text)):
            body = match.group("body").strip()
            equations.append(
                EquationOccurrence(
                    id=stable_id("equation", f"{work_id}:{asset_id}:tex:{len(equations)}"),
                    latex=body,
                )
            )
        references: list[ReferenceOccurrence] = []
        for match in _BIBITEM_RE.finditer(text):
            raw_reference = _clean_text(match.group("body"))
            if not raw_reference:
                continue
            references.append(
                ReferenceOccurrence(
                    id=stable_id(
                        "reference",
                        f"{work_id}:{asset_id}:tex:{len(references)}:{raw_reference}",
                    ),
                    order=len(references),
                    raw_text=raw_reference,
                    identifiers=infer_reference_identifiers(raw_reference),
                )
            )
        return ParsedDocument(
            work_id=work_id,
            asset_id=asset_id,
            source_format="latex",
            parser=self.name,
            parser_version=self.version,
            sections=sections,
            equations=equations,
            references=references,
        )
