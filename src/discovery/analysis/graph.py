from __future__ import annotations

from collections import deque

from pydantic import BaseModel, ConfigDict, Field


class DirectedGraphStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: int = Field(ge=0)
    edges: int = Field(ge=0)
    in_degree: dict[str, int] = Field(default_factory=dict)
    out_degree: dict[str, int] = Field(default_factory=dict)
    weak_components: list[list[str]] = Field(default_factory=list)


def directed_graph_stats(edges: list[tuple[str, str]]) -> DirectedGraphStats:
    nodes = {node for edge in edges for node in edge}
    outgoing: dict[str, set[str]] = {node: set() for node in nodes}
    incoming: dict[str, set[str]] = {node: set() for node in nodes}
    undirected: dict[str, set[str]] = {node: set() for node in nodes}
    for source, target in edges:
        outgoing[source].add(target)
        incoming[target].add(source)
        undirected[source].add(target)
        undirected[target].add(source)
    seen: set[str] = set()
    components: list[list[str]] = []
    for start in sorted(nodes):
        if start in seen:
            continue
        queue: deque[str] = deque([start])
        component: list[str] = []
        while queue:
            node = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            component.append(node)
            queue.extend(sorted(undirected[node] - seen))
        components.append(sorted(component))
    return DirectedGraphStats(
        nodes=len(nodes),
        edges=len(edges),
        in_degree={node: len(incoming[node]) for node in sorted(nodes)},
        out_degree={node: len(outgoing[node]) for node in sorted(nodes)},
        weak_components=components,
    )


def bibliographic_coupling(edges: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
    references: dict[str, set[str]] = {}
    for source, target in edges:
        references.setdefault(source, set()).add(target)
    works = sorted(references)
    result: dict[tuple[str, str], int] = {}
    for index, left in enumerate(works):
        for right in works[index + 1 :]:
            shared = len(references[left] & references[right])
            if shared:
                result[(left, right)] = shared
    return result


def co_citation(edges: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
    citing_by_target: dict[str, set[str]] = {}
    for source, target in edges:
        citing_by_target.setdefault(target, set()).add(source)
    targets = sorted(citing_by_target)
    result: dict[tuple[str, str], int] = {}
    for index, left in enumerate(targets):
        for right in targets[index + 1 :]:
            shared = len(citing_by_target[left] & citing_by_target[right])
            if shared:
                result[(left, right)] = shared
    return result
