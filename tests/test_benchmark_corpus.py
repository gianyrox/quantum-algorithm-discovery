import pytest
from pydantic import ValidationError

from discovery.evaluation.corpus import (
    BenchmarkCorpus,
    BenchmarkSplit,
    BenchmarkWork,
    SelectionStatus,
)


def test_empty_pilot_corpus_is_valid() -> None:
    corpus = BenchmarkCorpus(
        benchmark_name="cross-disciplinary-scientific-problems",
        version="0.1",
        description="Pilot benchmark",
        works=[],
    )

    assert corpus.version == "0.1"
    assert corpus.works == []


def test_benchmark_work_preserves_sampling_metadata() -> None:
    work = BenchmarkWork(
        benchmark_work_id="pilot-001",
        title="Example scientific work",
        discipline="physics",
        publication_year=2020,
        split=BenchmarkSplit.PILOT,
        status=SelectionStatus.CANDIDATE,
        selection_reason="Chosen to test spectral computational structure.",
        selection_method="manual breadth-first pilot sampling",
        desired_diversity_axes=["spectral", "continuous"],
    )

    assert work.discipline == "physics"
    assert work.status == SelectionStatus.CANDIDATE


def test_selection_reason_is_required() -> None:
    with pytest.raises(ValidationError):
        BenchmarkWork(
            benchmark_work_id="pilot-002",
            title="Example",
            discipline="chemistry",
            selection_method="manual",
        )
