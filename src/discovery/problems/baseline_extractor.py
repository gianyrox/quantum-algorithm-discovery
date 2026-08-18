from __future__ import annotations

import re

from discovery.core.evidence import Evidence, EvidenceLocation
from discovery.core.ids import stable_id
from discovery.documents.schema import ParsedDocument
from discovery.documents.text import document_text
from discovery.problems.enums import EvidenceKind, ExtractionMethod, TaskFamily
from discovery.problems.evidence import EvidenceSpan, FieldConfidence
from discovery.problems.schema import MathematicalObject, ProblemInstance

_TASK_PATTERNS: dict[TaskFamily, tuple[str, ...]] = {
    TaskFamily.OPTIMIZATION: ("optimiz", "minimiz", "maximiz", "objective function"),
    TaskFamily.SEARCH: ("search problem", "find a", "locate a"),
    TaskFamily.SAMPLING: ("sampling", "draw samples", "sample from"),
    TaskFamily.ESTIMATION: ("estimate", "estimation", "estimator"),
    TaskFamily.INFERENCE: ("inference", "posterior", "infer"),
    TaskFamily.SIMULATION: ("simulate", "simulation", "numerical model"),
    TaskFamily.PREDICTION: ("predict", "forecast"),
    TaskFamily.CLASSIFICATION: ("classif", "label prediction"),
    TaskFamily.CONTROL: ("optimal control", "control policy", "controller"),
    TaskFamily.INVERSE_PROBLEM: ("inverse problem", "reconstruct", "tomograph"),
    TaskFamily.LINEAR_SYSTEM: ("linear system", "solve ax", "linear solve"),
    TaskFamily.EIGENPROBLEM: ("eigenvalue", "eigenvector", "eigensystem"),
    TaskFamily.SPECTRAL_PROBLEM: ("spectrum", "spectral decomposition", "spectral problem"),
    TaskFamily.DIFFERENTIAL_EQUATION: ("differential equation", "pde", "ode"),
    TaskFamily.STOCHASTIC_PROCESS: ("stochastic process", "markov process", "markov chain"),
    TaskFamily.GRAPH_PROBLEM: ("graph problem", "network flow", "shortest path"),
    TaskFamily.CONSTRAINT_SATISFACTION: (
        "constraint satisfaction",
        "satisfiability",
        "feasible assignment",
    ),
    TaskFamily.PLANNING: ("planning problem", "trajectory planning", "schedule"),
    TaskFamily.DYNAMICAL_SYSTEM: ("dynamical system", "phase space", "trajectory"),
    TaskFamily.RARE_EVENT: ("rare event", "rare-event"),
    TaskFamily.INTEGRATION: ("numerical integration", "integral estimation", "quadrature"),
    TaskFamily.COUNTING: ("counting problem", "count the number", "partition function"),
}

_OPERATION_PATTERNS: dict[str, tuple[str, ...]] = {
    "matrix-vector multiplication": ("matrix-vector", "matrix vector"),
    "linear solve": ("linear system", "linear solve"),
    "eigenvalue computation": ("eigenvalue", "eigensolver"),
    "sampling": ("sampling", "monte carlo"),
    "numerical integration": ("quadrature", "numerical integration"),
    "gradient evaluation": ("gradient", "backpropagation"),
    "graph traversal": ("graph traversal", "breadth-first", "depth-first"),
    "optimization update": ("gradient descent", "newton method", "optimization iteration"),
    "time stepping": ("time step", "time-stepping", "integrator"),
}

_STRUCTURE_PATTERNS: dict[str, tuple[str, ...]] = {
    "sparse": ("sparse", "sparsity"),
    "low-rank": ("low-rank", "low rank"),
    "symmetric": ("symmetric matrix", "symmetry"),
    "local": ("local interaction", "locality"),
    "convex": ("convex",),
    "non-convex": ("nonconvex", "non-convex"),
    "graph-structured": ("graph", "network"),
    "high-dimensional": ("high-dimensional", "high dimensional"),
    "ill-conditioned": ("ill-conditioned", "ill conditioned"),
    "periodic": ("periodic", "periodicity"),
}

_MATH_OBJECT_PATTERNS: dict[str, tuple[str, ...]] = {
    "matrix": ("matrix", "matrices"),
    "graph": ("graph", "network"),
    "tensor": ("tensor",),
    "probability_distribution": ("probability distribution", "density", "posterior"),
    "differential_equation": ("differential equation", "pde", "ode"),
    "operator": ("operator",),
    "hamiltonian": ("hamiltonian",),
    "markov_chain": ("markov chain",),
    "optimization_landscape": ("loss landscape", "energy landscape", "objective landscape"),
}


def _contains(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(pattern.casefold() in lowered for pattern in patterns)


def _evidence_quote(text: str, patterns: tuple[str, ...]) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
    for sentence in sentences:
        if _contains(sentence, patterns):
            return sentence[:700]
    return None


def _field_span(
    document: ParsedDocument, field: str, patterns: tuple[str, ...], confidence: float
) -> EvidenceSpan | None:
    for section in document.sections:
        lowered = section.text.casefold()
        for pattern in patterns:
            index = lowered.find(pattern.casefold())
            if index < 0:
                continue
            start = max(0, index - 180)
            end = min(len(section.text), index + len(pattern) + 360)
            return EvidenceSpan(
                field=field,
                section_id=section.id,
                start_char=start,
                end_char=end,
                text=section.text[start:end],
                confidence=confidence,
                extraction_rule=f"keyword:{pattern}",
            )
    return None


class TransparentBaselineProblemExtractor:
    """Low-confidence extraction baseline for pipeline/evaluation plumbing.

    It is deliberately simple and auditable. It is not intended to replace
    human annotations or a scientifically evaluated structured extractor.
    """

    name = "transparent-keyword-baseline"
    version = "0.10"

    def extract(self, document: ParsedDocument) -> list[ProblemInstance]:
        text = document_text(document)
        if not text.strip():
            return []
        detected: list[tuple[TaskFamily, tuple[str, ...]]] = [
            (family, patterns)
            for family, patterns in _TASK_PATTERNS.items()
            if _contains(text, patterns)
        ]
        if not detected:
            return []

        operations = [
            name for name, patterns in _OPERATION_PATTERNS.items() if _contains(text, patterns)
        ]
        structures = [
            name for name, patterns in _STRUCTURE_PATTERNS.items() if _contains(text, patterns)
        ]
        math_objects = [
            MathematicalObject(name=name.replace("_", " "), object_type=name)
            for name, patterns in _MATH_OBJECT_PATTERNS.items()
            if _contains(text, patterns)
        ]
        problems: list[ProblemInstance] = []
        for index, (family, patterns) in enumerate(detected[:3]):
            quote = _evidence_quote(text, patterns)
            confidence = min(0.55, 0.20 + 0.05 * len(operations) + 0.04 * len(structures))
            task_span = _field_span(document, "task_family", patterns, confidence)
            spans = [task_span] if task_span is not None else []
            field_confidence = [
                FieldConfidence(
                    field="task_family",
                    confidence=confidence,
                    evidence_count=len(spans),
                    unresolved=True,
                )
            ]
            problems.append(
                ProblemInstance(
                    id=stable_id(
                        "baseline-problem",
                        f"{document.work_id}:{document.asset_id}:{family.value}:{index}",
                    ),
                    source_work_id=document.work_id,
                    natural_language_statement=quote or f"Candidate {family.value} problem.",
                    task_family=family,
                    mathematical_objects=math_objects,
                    structural_properties=structures,
                    algorithmic_operations=operations,
                    evidence=[
                        Evidence(
                            kind=EvidenceKind.OTHER,
                            location=EvidenceLocation(quote=quote),
                            source_identifier=document.asset_id,
                            note="Rule-based candidate evidence; requires human review.",
                        )
                    ],
                    evidence_spans=spans,
                    field_confidence=field_confidence,
                    extraction_method=ExtractionMethod.RULE_BASED,
                    extractor=self.name,
                    extractor_version=self.version,
                    extraction_notes=(
                        "Transparent keyword baseline. Empty fields mean not extracted, not absent."
                    ),
                    confidence=confidence,
                    unresolved_questions=[
                        "Verify task formulation against the source.",
                        "Identify explicit inputs, outputs, access model, and scaling parameters.",
                        "Verify mathematical structures from equations/methods rather than "
                        "keywords.",
                    ],
                )
            )
        return problems
