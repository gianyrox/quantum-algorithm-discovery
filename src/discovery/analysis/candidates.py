from __future__ import annotations

from discovery.analysis.similarity import SimilarityEvidence
from discovery.core.ids import stable_id
from discovery.discovery.ranking import cross_domain_candidate_score
from discovery.discovery.schema import CrossDomainCandidate
from discovery.problems.schema import ProblemInstance


def generate_cross_domain_candidates(
    problems: dict[str, ProblemInstance],
    similarities: dict[tuple[str, str], SimilarityEvidence],
    disciplines: dict[str, str],
    *,
    minimum_structural_score: float = 0.35,
    maximum_lexical_similarity: float = 0.65,
    maximum_citation_connectivity: float = 0.50,
) -> list[CrossDomainCandidate]:
    candidates: list[CrossDomainCandidate] = []
    for (left_id, right_id), evidence in similarities.items():
        left_field = disciplines.get(left_id, "unknown")
        right_field = disciplines.get(right_id, "unknown")
        different = left_field != right_field and "unknown" not in {left_field, right_field}
        if not different:
            continue
        if evidence.structural_score() < minimum_structural_score:
            continue
        if evidence.lexical > maximum_lexical_similarity:
            continue
        if evidence.citation_connectivity > maximum_citation_connectivity:
            continue
        left = problems[left_id]
        right = problems[right_id]
        left_structures = {
            *left.structural_properties,
            *left.operators,
            *left.algorithmic_operations,
            *(item.object_type for item in left.mathematical_objects),
        }
        right_structures = {
            *right.structural_properties,
            *right.operators,
            *right.algorithmic_operations,
            *(item.object_type for item in right.mathematical_objects),
        }
        shared = sorted(
            {item.casefold() for item in left_structures}
            & {item.casefold() for item in right_structures}
        )
        score = cross_domain_candidate_score(evidence, different_disciplines=True)
        candidates.append(
            CrossDomainCandidate(
                id=stable_id("cross-domain-candidate", f"{left_id}:{right_id}"),
                problem_a_id=left_id,
                problem_b_id=right_id,
                field_a=left_field,
                field_b=right_field,
                similarity=evidence,
                shared_structures=shared,
                candidate_score=score,
                evidence=[
                    "High structural score relative to configured threshold.",
                    "Different discipline labels.",
                    "Lexical similarity and citation connectivity remain below configured caps.",
                ],
            )
        )
    return sorted(candidates, key=lambda item: (-item.candidate_score, item.id))
