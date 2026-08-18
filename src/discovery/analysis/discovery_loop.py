from __future__ import annotations

from itertools import combinations

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.family_builder import FamilyBuildConfig, build_problem_families
from discovery.analysis.multiview import MultiViewSimilarity, SimilarityWeights, compare_problems
from discovery.analysis.relations import RelationHypothesis, classify_relation
from discovery.problems.family import ProblemFamily
from discovery.problems.schema import ProblemInstance


class StructureDiscoveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_count: int = Field(ge=0)
    pair_count: int = Field(ge=0)
    similarities: list[MultiViewSimilarity] = Field(default_factory=list)
    families: list[ProblemFamily] = Field(default_factory=list)
    relation_hypotheses: list[RelationHypothesis] = Field(default_factory=list)


def discover_structure(
    problems: list[ProblemInstance],
    *,
    discipline_by_problem: dict[str, str] | None = None,
    citation_connectivity: dict[tuple[str, str], float] | None = None,
    similarity_weights: SimilarityWeights | None = None,
    family_config: FamilyBuildConfig | None = None,
) -> StructureDiscoveryResult:
    del discipline_by_problem  # reserved for cross-domain candidate filtering/review strata
    citation_connectivity = citation_connectivity or {}
    problem_map = {item.id: item for item in problems}
    similarities: list[MultiViewSimilarity] = []
    for left, right in combinations(problems, 2):
        connectivity = citation_connectivity.get((left.id, right.id), 0.0)
        similarity = compare_problems(
            left,
            right,
            citation_connectivity=connectivity,
            weights=similarity_weights,
        )
        similarities.append(similarity)
    families = build_problem_families(problem_map, similarities, config=family_config)
    hypotheses = [classify_relation(item) for item in similarities]
    return StructureDiscoveryResult(
        problem_count=len(problems),
        pair_count=len(similarities),
        similarities=similarities,
        families=families,
        relation_hypotheses=hypotheses,
    )
