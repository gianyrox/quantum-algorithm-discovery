from __future__ import annotations

from collections.abc import Callable

from discovery.pipeline.schema import PipelineStage, StageResult

StageCallable = Callable[[], StageResult]


class PipelineRunner:
    """Small sequential orchestrator; heavy scheduling remains an infrastructure choice."""

    def __init__(self) -> None:
        self._stages: list[tuple[PipelineStage, StageCallable]] = []

    def add(self, stage: PipelineStage, callable_: StageCallable) -> PipelineRunner:
        self._stages.append((stage, callable_))
        return self

    def run(self) -> list[StageResult]:
        results: list[StageResult] = []
        for expected, callable_ in self._stages:
            result = callable_()
            if result.stage != expected:
                raise ValueError(f"stage returned {result.stage}; expected {expected}")
            results.append(result)
            if result.status == "failed":
                break
        return results
