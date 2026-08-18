from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from discovery.experiments.schema import ExperimentRun
from discovery.storage.models import ExperimentRunRow


class ExperimentTracker:
    def __init__(self, session: Session) -> None:
        self.session = session

    def start(
        self, name: str, experiment_type: str, config: dict[str, object] | None = None
    ) -> ExperimentRun:
        run = ExperimentRun(
            id=str(uuid4()),
            name=name,
            experiment_type=experiment_type,
            config=config or {},
        )
        self.session.add(
            ExperimentRunRow(
                id=run.id,
                name=run.name,
                experiment_type=run.experiment_type,
                status=run.status,
                started_at=run.started_at,
                config_json=run.config,
                metrics_json={},
                artifacts_json=[],
            )
        )
        self.session.flush()
        return run

    def finish(self, run_id: str, metrics: dict[str, object] | None = None) -> ExperimentRun:
        row = self.session.get(ExperimentRunRow, run_id)
        if row is None:
            raise KeyError(run_id)
        row.status = "completed"
        row.completed_at = datetime.now(UTC)
        row.metrics_json = metrics or {}
        self.session.flush()
        return ExperimentRun(
            id=row.id,
            name=row.name,
            experiment_type=row.experiment_type,
            status=row.status,
            started_at=row.started_at,
            completed_at=row.completed_at,
            config=row.config_json,
            metrics=row.metrics_json,
            artifacts=[],
            notes=row.notes,
        )
