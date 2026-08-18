from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class ProblemQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str
    completeness: float = Field(ge=0, le=1)
    evidence_coverage: float = Field(ge=0, le=1)
    ambiguity_flags: list[str] = Field(default_factory=list)
    missing_high_value_fields: list[str] = Field(default_factory=list)


_HIGH_VALUE = (
    "inputs",
    "outputs",
    "objective",
    "constraints",
    "access_model",
    "mathematical_objects",
    "algorithmic_operations",
    "reported_bottlenecks",
)


def assess_problem_quality(problem: ProblemInstance) -> ProblemQualityReport:
    populated = 0
    missing: list[str] = []
    for field in _HIGH_VALUE:
        value = getattr(problem, field)
        if value not in (None, "", [], {}):
            populated += 1
        else:
            missing.append(field)
    completeness = populated / len(_HIGH_VALUE)
    evidence_fields = {span.field for span in problem.evidence_spans}
    evidence_coverage = len(evidence_fields & set(_HIGH_VALUE)) / len(_HIGH_VALUE)
    ambiguity: list[str] = []
    if problem.task_family.value == "unknown":
        ambiguity.append("unknown task family")
    if not problem.source_version_id:
        ambiguity.append("source version not pinned")
    if problem.confidence < 0.5:
        ambiguity.append("low overall extraction confidence")
    return ProblemQualityReport(
        problem_id=problem.id,
        completeness=round(completeness, 6),
        evidence_coverage=round(evidence_coverage, 6),
        ambiguity_flags=ambiguity,
        missing_high_value_fields=missing,
    )
