from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from discovery.documents.schema import ParsedDocument
from discovery.problems.extraction import ProblemExtractor
from discovery.problems.schema import ProblemInstance


class ExtractorVote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extractor: str
    version: str
    problem_ids: list[str] = Field(default_factory=list)


class EnsembleExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_id: str
    problems: list[ProblemInstance] = Field(default_factory=list)
    votes: list[ExtractorVote] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)


def _problem_key(problem: ProblemInstance) -> tuple[str, str]:
    statement = " ".join(problem.natural_language_statement.casefold().split())
    return problem.task_family.value, statement[:240]


class ProblemExtractorEnsemble:
    """Runs multiple extractors without pretending disagreement is consensus."""

    def __init__(self, extractors: Iterable[ProblemExtractor]) -> None:
        self.extractors = list(extractors)

    def extract(self, document: ParsedDocument) -> EnsembleExtractionResult:
        seen: dict[tuple[str, str], ProblemInstance] = {}
        votes: list[ExtractorVote] = []
        families_by_extractor: dict[str, set[str]] = {}
        for extractor in self.extractors:
            problems = extractor.extract(document)
            label = f"{extractor.name}@{extractor.version}"
            votes.append(
                ExtractorVote(
                    extractor=extractor.name,
                    version=extractor.version,
                    problem_ids=[item.id for item in problems],
                )
            )
            families_by_extractor[label] = {item.task_family.value for item in problems}
            for problem in problems:
                key = _problem_key(problem)
                incumbent = seen.get(key)
                if incumbent is None or problem.confidence > incumbent.confidence:
                    seen[key] = problem
        disagreements: list[str] = []
        family_sets = list(families_by_extractor.items())
        for index, (left_name, left_families) in enumerate(family_sets):
            for right_name, right_families in family_sets[index + 1 :]:
                if left_families != right_families:
                    disagreements.append(
                        f"task-family disagreement: {left_name}={sorted(left_families)}; "
                        f"{right_name}={sorted(right_families)}"
                    )
        problems = sorted(seen.values(), key=lambda item: (item.task_family.value, item.id))
        return EnsembleExtractionResult(
            work_id=document.work_id,
            problems=problems,
            votes=votes,
            disagreements=disagreements,
        )
