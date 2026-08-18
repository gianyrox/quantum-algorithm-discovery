from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from discovery.analysis.multiview import MultiViewSimilarity
from discovery.core.ids import stable_id
from discovery.problems.family import ProblemFamily
from discovery.problems.schema import ProblemInstance


class FamilyBuildConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_similarity: float = Field(default=0.42, ge=0, le=1)
    minimum_members: int = Field(default=2, ge=2)


def _components(
    problem_ids: list[str],
    similarities: list[MultiViewSimilarity],
    threshold: float,
) -> list[list[str]]:
    adjacency: dict[str, set[str]] = {item: set() for item in problem_ids}
    for similarity in similarities:
        if similarity.aggregate_score >= threshold:
            adjacency.setdefault(similarity.problem_a_id, set()).add(similarity.problem_b_id)
            adjacency.setdefault(similarity.problem_b_id, set()).add(similarity.problem_a_id)
    seen: set[str] = set()
    result: list[list[str]] = []
    for start in problem_ids:
        if start in seen:
            continue
        stack = [start]
        component: list[str] = []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            component.append(node)
            stack.extend(adjacency.get(node, set()) - seen)
        result.append(sorted(component))
    return result


def build_problem_families(
    problems: dict[str, ProblemInstance],
    similarities: list[MultiViewSimilarity],
    *,
    config: FamilyBuildConfig | None = None,
) -> list[ProblemFamily]:
    config = config or FamilyBuildConfig()
    components = _components(sorted(problems), similarities, config.minimum_similarity)
    families: list[ProblemFamily] = []
    for component in components:
        if len(component) < config.minimum_members:
            continue
        members = [problems[item] for item in component]
        tasks = Counter(item.task_family.value for item in members)
        operations = Counter(
            op.casefold() for item in members for op in item.algorithmic_operations
        )
        structures = Counter(
            structure.casefold() for item in members for structure in item.structural_properties
        )
        shared_operations = sorted(item for item, count in operations.items() if count >= 2)
        shared_structures = sorted(item for item, count in structures.items() if count >= 2)
        family_id = stable_id("problem-family-v010", ":".join(component))
        dominant_task = tasks.most_common(1)[0][0]
        families.append(
            ProblemFamily(
                id=family_id,
                name=f"{dominant_task} structural family",
                description=(
                    "Candidate family induced by multi-view structural similarity. "
                    "Membership is a discovery hypothesis requiring scientific review."
                ),
                problem_ids=component,
                shared_task_families=sorted(tasks),
                shared_mathematical_structures=shared_structures,
                shared_operations=shared_operations,
                evidence=[
                    f"component threshold={config.minimum_similarity:.3f}",
                    f"member count={len(component)}",
                ],
            )
        )
    return families
