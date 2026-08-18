from __future__ import annotations

from discovery.core.ids import stable_id
from discovery.problems.family import ProblemFamily
from discovery.problems.schema import ProblemInstance


def build_candidate_families(
    components: list[list[str]],
    problems: dict[str, ProblemInstance],
) -> list[ProblemFamily]:
    families: list[ProblemFamily] = []
    for index, component in enumerate(components, start=1):
        if len(component) < 2:
            continue
        task_sets = [{problems[problem_id].task_family.value} for problem_id in component]
        common_tasks = sorted(set.intersection(*task_sets)) if task_sets else []
        structure_sets = [
            {item.casefold() for item in problems[problem_id].structural_properties}
            for problem_id in component
        ]
        operation_sets = [
            {item.casefold() for item in problems[problem_id].algorithmic_operations}
            for problem_id in component
        ]
        common_structures = sorted(set.intersection(*structure_sets)) if structure_sets else []
        common_operations = sorted(set.intersection(*operation_sets)) if operation_sets else []
        family_id = stable_id("problem-family", ":".join(sorted(component)))
        families.append(
            ProblemFamily(
                id=family_id,
                name=f"Candidate problem family {index}",
                description=(
                    "Automatically clustered candidate family. Membership is a hypothesis "
                    "requiring "
                    "structural and domain-expert review."
                ),
                problem_ids=sorted(component),
                shared_task_families=common_tasks,
                shared_mathematical_structures=common_structures,
                shared_operations=common_operations,
                evidence=["Generated from a configured similarity threshold; not equivalence."],
                status="candidate",
            )
        )
    return families
