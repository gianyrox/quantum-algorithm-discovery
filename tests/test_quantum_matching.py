from __future__ import annotations

from discovery.quantum.matching import baseline_quantum_match
from discovery.quantum.schema import QuantumAlgorithm, QuantumOpportunityCategory


def test_quantum_match_stays_unresolved_without_advantage_review(example_problem) -> None:
    algorithm = QuantumAlgorithm(
        id="qa-1",
        name="Example spectral algorithm",
        family="spectral",
        problem_classes=["eigenproblem"],
        required_structures=["matrix-vector multiplication"],
    )
    match = baseline_quantum_match(example_problem, algorithm)
    assert match.category == QuantumOpportunityCategory.UNRESOLVED
    assert match.representational_compatibility == 1.0
    assert match.notes
