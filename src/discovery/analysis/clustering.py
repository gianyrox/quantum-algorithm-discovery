from __future__ import annotations

from discovery.analysis.similarity import SimilarityEvidence


def connected_components(
    problem_ids: list[str],
    similarities: dict[tuple[str, str], SimilarityEvidence],
    *,
    threshold: float = 0.55,
) -> list[list[str]]:
    adjacency: dict[str, set[str]] = {problem_id: set() for problem_id in problem_ids}
    for (a, b), evidence in similarities.items():
        if evidence.structural_score() >= threshold:
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)

    components: list[list[str]] = []
    seen: set[str] = set()
    for start in problem_ids:
        if start in seen:
            continue
        stack = [start]
        group: list[str] = []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            group.append(node)
            stack.extend(sorted(adjacency.get(node, set()) - seen, reverse=True))
        components.append(sorted(group))
    return components
