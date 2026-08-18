from __future__ import annotations

from discovery.experiments.tracker import ExperimentTracker
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_experiment_tracker_roundtrip(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        tracker = ExperimentTracker(session)
        run = tracker.start("pilot", "problem-extraction", {"split": "pilot"})
        finished = tracker.finish(run.id, {"accuracy": 0.75})
        assert finished.status == "completed"
        assert finished.metrics["accuracy"] == 0.75
