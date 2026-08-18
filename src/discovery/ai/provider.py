from __future__ import annotations

from typing import Protocol

from discovery.ai.schema import AlgorithmProposal
from discovery.problems.family import ProblemFamily
from discovery.quantum.schema import QuantumAlgorithm, QuantumPrimitive


class AlgorithmDiscoveryReasoner(Protocol):
    name: str
    version: str

    def propose(
        self,
        family: ProblemFamily,
        known_algorithms: list[QuantumAlgorithm],
        primitives: list[QuantumPrimitive],
    ) -> list[AlgorithmProposal]: ...
