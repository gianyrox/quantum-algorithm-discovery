from __future__ import annotations

import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from discovery.documents.schema import ParsedDocument


class DocumentIntelligence(BaseModel):
    """Loss-minimizing structural summary of a parsed scientific document."""

    model_config = ConfigDict(extra="forbid")

    work_id: str
    section_count: int = Field(ge=0)
    equation_count: int = Field(ge=0)
    figure_count: int = Field(ge=0)
    table_count: int = Field(ge=0)
    reference_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    section_types: dict[str, int] = Field(default_factory=dict)
    math_dense_sections: list[str] = Field(default_factory=list)
    likely_problem_sections: list[str] = Field(default_factory=list)
    likely_method_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


_PROBLEM_HINTS = (
    "problem",
    "objective",
    "we seek",
    "we solve",
    "we consider",
    "estimate",
    "infer",
    "optimize",
    "simulate",
    "predict",
    "control",
    "reconstruct",
)
_METHOD_HINTS = (
    "method",
    "algorithm",
    "procedure",
    "solver",
    "implementation",
    "numerical",
    "experimental setup",
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9_'-]*", text)


def analyze_document(document: ParsedDocument) -> DocumentIntelligence:
    equation_sections = Counter(
        item.section_id for item in document.equations if item.section_id is not None
    )
    section_types = Counter((section.section_type or "unknown") for section in document.sections)
    problem_sections: list[str] = []
    method_sections: list[str] = []
    math_dense: list[str] = []
    total_words = 0
    for section in document.sections:
        text = section.text.casefold()
        total_words += len(_tokens(section.text))
        if any(hint in text for hint in _PROBLEM_HINTS):
            problem_sections.append(section.id)
        if any(hint in text for hint in _METHOD_HINTS):
            method_sections.append(section.id)
        if equation_sections[section.id] >= 2:
            math_dense.append(section.id)
    warnings = list(document.warnings)
    if not document.sections:
        warnings.append("document contains no parsed sections")
    if not document.references:
        warnings.append("document contains no parsed references")
    return DocumentIntelligence(
        work_id=document.work_id,
        section_count=len(document.sections),
        equation_count=len(document.equations),
        figure_count=len(document.figures),
        table_count=len(document.tables),
        reference_count=len(document.references),
        word_count=total_words,
        section_types=dict(sorted(section_types.items())),
        math_dense_sections=sorted(math_dense),
        likely_problem_sections=sorted(problem_sections),
        likely_method_sections=sorted(method_sections),
        warnings=warnings,
    )
