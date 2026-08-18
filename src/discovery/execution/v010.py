from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.discovery_loop import StructureDiscoveryResult, discover_structure
from discovery.coverage.active import ActiveRetrievalPlanner, RetrievalPriority
from discovery.coverage.feedback import FeedbackDecision, FeedbackLoop
from discovery.coverage.saturation import DiscoveryYield
from discovery.coverage.strata import StratifiedCoverageReport, build_coverage_report
from discovery.documents.intelligence import DocumentIntelligence, analyze_document
from discovery.documents.schema import ParsedDocument
from discovery.problems.quality import ProblemQualityReport, assess_problem_quality
from discovery.problems.schema import ProblemInstance


class PreQuantumStage(StrEnum):
    RETRIEVAL = "retrieval"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    PROBLEM_EXTRACTION = "problem_extraction"
    MATHEMATICAL_STRUCTURE = "mathematical_structure"
    STRUCTURAL_DISCOVERY = "structural_discovery"
    COVERAGE_FEEDBACK = "coverage_feedback"


class PreQuantumAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_intelligence: list[DocumentIntelligence] = Field(default_factory=list)
    problem_quality: list[ProblemQualityReport] = Field(default_factory=list)
    structure_discovery: StructureDiscoveryResult
    coverage: StratifiedCoverageReport
    priorities: list[RetrievalPriority] = Field(default_factory=list)
    feedback: FeedbackDecision
    notes: list[str] = Field(default_factory=list)


def analyze_pre_quantum_corpus(
    documents: list[ParsedDocument],
    problems: list[ProblemInstance],
    coverage_records: list[dict[str, object]],
    retrieval_scopes: list[dict[str, object]],
    yields: list[DiscoveryYield],
    *,
    strata_stable: bool,
    unknown_terms: list[str] | None = None,
) -> PreQuantumAnalysisResult:
    intelligence = [analyze_document(item) for item in documents]
    quality = [assess_problem_quality(item) for item in problems]
    structure = discover_structure(problems)
    coverage = build_coverage_report(coverage_records)
    priorities = ActiveRetrievalPlanner().prioritize(retrieval_scopes)
    feedback = FeedbackLoop().decide(
        yields,
        priorities,
        strata_stable=strata_stable,
        unknown_terms=unknown_terms,
    )
    return PreQuantumAnalysisResult(
        document_intelligence=intelligence,
        problem_quality=quality,
        structure_discovery=structure,
        coverage=coverage,
        priorities=priorities,
        feedback=feedback,
        notes=[
            "This analysis is intentionally pre-quantum.",
            (
                "Similarity and family assignments are candidate structures, "
                "not scientific equivalence claims."
            ),
        ],
    )
