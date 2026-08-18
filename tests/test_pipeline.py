from __future__ import annotations

from discovery.pipeline.runner import PipelineRunner
from discovery.pipeline.schema import PipelineStage, StageResult


def test_pipeline_stops_after_failed_stage() -> None:
    runner = PipelineRunner()
    runner.add(
        PipelineStage.RETRIEVAL,
        lambda: StageResult(stage=PipelineStage.RETRIEVAL, status="completed"),
    )
    runner.add(
        PipelineStage.CORPUS,
        lambda: StageResult(stage=PipelineStage.CORPUS, status="failed"),
    )
    runner.add(
        PipelineStage.DOCUMENTS,
        lambda: StageResult(stage=PipelineStage.DOCUMENTS, status="completed"),
    )
    results = runner.run()
    assert [item.stage for item in results] == [PipelineStage.RETRIEVAL, PipelineStage.CORPUS]
