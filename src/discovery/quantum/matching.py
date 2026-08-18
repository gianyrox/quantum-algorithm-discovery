from __future__ import annotations

from discovery.problems.schema import ProblemInstance
from discovery.quantum.schema import QuantumAlgorithm, QuantumMatch, QuantumOpportunityCategory


def _overlap(required: set[str], observed: set[str]) -> float:
    if not required:
        return 0.5
    return len(required & observed) / len(required)


def baseline_quantum_match(problem: ProblemInstance, algorithm: QuantumAlgorithm) -> QuantumMatch:
    observed = {
        problem.task_family.value.casefold(),
        *(item.casefold() for item in problem.structural_properties),
        *(item.casefold() for item in problem.operators),
        *(item.casefold() for item in problem.algorithmic_operations),
        *(item.object_type.casefold() for item in problem.mathematical_objects),
    }
    required = {item.casefold() for item in algorithm.required_structures}
    classes = {item.casefold() for item in algorithm.problem_classes}
    task_score = 1.0 if problem.task_family.value.casefold() in classes else 0.25
    structure_score = _overlap(required, observed)
    if algorithm.access_model is None or problem.access_model is None:
        access_score = 0.5
    else:
        access_score = (
            1.0 if algorithm.access_model.casefold() == problem.access_model.casefold() else 0.0
        )
    return QuantumMatch(
        problem_id=problem.id,
        algorithm_id=algorithm.id,
        category=QuantumOpportunityCategory.UNRESOLVED,
        representational_compatibility=task_score,
        access_model_compatibility=access_score,
        structural_compatibility=structure_score,
        notes=[
            "Baseline structural screen only; it does not establish applicability or advantage.",
            "Classical baselines, data loading, readout, and dequantization require "
            "separate review.",
        ],
    )
