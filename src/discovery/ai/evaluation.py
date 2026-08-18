from __future__ import annotations

from typing import Protocol

from discovery.ai.schema import AlgorithmProposal, ProposalEvaluation


class ProposalEvaluator(Protocol):
    name: str
    version: str

    def evaluate(self, proposal: AlgorithmProposal) -> ProposalEvaluation: ...


class UnresolvedProposalEvaluator:
    """Pipeline baseline that intentionally makes no scientific validity claim."""

    name = "unresolved-baseline"
    version = "0.3"

    def evaluate(self, proposal: AlgorithmProposal) -> ProposalEvaluation:
        return ProposalEvaluation(
            proposal_id=proposal.id,
            conclusions=[
                "No validity conclusion has been established.",
                "Requires mathematical proof, classical comparison, and dequantization review.",
            ],
        )
