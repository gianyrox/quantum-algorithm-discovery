from __future__ import annotations

from sqlalchemy.orm import Session

from discovery.ai.evaluation import ProposalEvaluator
from discovery.ai.provider import AlgorithmDiscoveryReasoner
from discovery.ai.repository import AlgorithmProposalRepository
from discovery.ai.schema import AlgorithmProposal, ProposalEvaluation
from discovery.problems.family import ProblemFamily
from discovery.quantum.schema import QuantumAlgorithm, QuantumPrimitive


class AlgorithmDiscoveryService:
    def __init__(
        self,
        reasoner: AlgorithmDiscoveryReasoner,
        evaluator: ProposalEvaluator,
        session: Session | None = None,
    ) -> None:
        self.reasoner = reasoner
        self.evaluator = evaluator
        self.repository = AlgorithmProposalRepository(session) if session is not None else None

    def propose_and_evaluate(
        self,
        family: ProblemFamily,
        known_algorithms: list[QuantumAlgorithm],
        primitives: list[QuantumPrimitive],
    ) -> list[tuple[AlgorithmProposal, ProposalEvaluation]]:
        proposals = self.reasoner.propose(family, known_algorithms, primitives)
        results: list[tuple[AlgorithmProposal, ProposalEvaluation]] = []
        for proposal in proposals:
            evaluation = self.evaluator.evaluate(proposal)
            if self.repository is not None:
                self.repository.upsert(proposal)
                self.repository.add_evaluation(evaluation, evaluator=self.evaluator.name)
            results.append((proposal, evaluation))
        return results
