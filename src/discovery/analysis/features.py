from __future__ import annotations

import re

from discovery.analysis.local_embeddings import cosine_similarity
from discovery.analysis.similarity import SimilarityEvidence, jaccard
from discovery.problems.schema import ProblemInstance


def lexical_tokens(problem: ProblemInstance) -> set[str]:
    text = " ".join(
        [
            problem.natural_language_statement,
            problem.objective or "",
            *problem.inputs,
            *problem.outputs,
            *problem.constraints,
        ]
    )
    return {
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)
        if token.casefold() not in {"the", "and", "for", "with", "from", "that", "this"}
    }


def hybrid_similarity(
    left: ProblemInstance,
    right: ProblemInstance,
    *,
    left_embedding: list[float] | None = None,
    right_embedding: list[float] | None = None,
    citation_connectivity: float = 0.0,
) -> SimilarityEvidence:
    from discovery.analysis.similarity import baseline_problem_similarity

    evidence = baseline_problem_similarity(left, right)
    evidence.lexical = jaccard(lexical_tokens(left), lexical_tokens(right))
    if left_embedding is not None and right_embedding is not None:
        evidence.semantic = cosine_similarity(left_embedding, right_embedding)
    evidence.citation_connectivity = max(0.0, min(1.0, citation_connectivity))
    return evidence
