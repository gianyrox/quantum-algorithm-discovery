from __future__ import annotations

from discovery.analysis.similarity import SimilarityEvidence


def cross_domain_candidate_score(
    evidence: SimilarityEvidence,
    *,
    different_disciplines: bool,
) -> float:
    """Rank where structural similarity is high but lexical/citation coupling is low."""
    structural = evidence.structural_score()
    novelty = 0.5 * (1.0 - evidence.lexical) + 0.5 * (1.0 - evidence.citation_connectivity)
    discipline_bonus = 1.0 if different_disciplines else 0.5
    return round(min(1.0, 0.65 * structural + 0.25 * novelty + 0.10 * discipline_bonus), 6)
