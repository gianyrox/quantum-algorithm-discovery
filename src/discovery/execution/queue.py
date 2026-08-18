from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.execution.schema import ProcessingJob, ProcessingStage, QueueStats
from discovery.storage.models import ProcessingJobRow, WorkRow


class ProcessingQueue:
    """Small durable database-backed queue for resumable local research processing.

    The queue intentionally avoids pretending SQLite provides distributed-worker
    semantics. A single local worker is the default. PostgreSQL deployments can
    replace claim_next with SKIP LOCKED later without changing job records.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(
        self,
        *,
        work_id: str,
        stage: ProcessingStage,
        asset_id: str | None = None,
        priority: int = 0,
        max_attempts: int = 3,
        payload: dict[str, object] | None = None,
        available_at: datetime | None = None,
    ) -> ProcessingJob:
        if self.session.get(WorkRow, work_id) is None:
            raise KeyError(f"unknown canonical work: {work_id}")
        row_id = stable_id(
            "processing-job",
            f"{work_id}:{asset_id or ''}:{stage.value}",
        )
        row = self.session.get(ProcessingJobRow, row_id)
        if row is None:
            row = ProcessingJobRow(
                id=row_id,
                work_id=work_id,
                asset_id=asset_id,
                stage=stage.value,
                status="pending",
                priority=priority,
                attempts=0,
                max_attempts=max_attempts,
                available_at=available_at or datetime.now(UTC),
                payload_json=payload or {},
            )
        else:
            if row.status in {"completed", "running"}:
                return self._model(row)
            row.status = "pending"
            row.priority = priority
            row.max_attempts = max_attempts
            row.available_at = available_at or datetime.now(UTC)
            row.payload_json = payload or row.payload_json
            row.error = None
        self.session.add(row)
        self.session.flush()
        return self._model(row)

    def claim_next(
        self,
        *,
        stages: list[ProcessingStage] | None = None,
    ) -> ProcessingJob | None:
        now = datetime.now(UTC)
        stmt = (
            select(ProcessingJobRow)
            .where(
                ProcessingJobRow.status == "pending",
                ProcessingJobRow.available_at <= now,
                ProcessingJobRow.attempts < ProcessingJobRow.max_attempts,
            )
            .order_by(
                ProcessingJobRow.priority.desc(),
                ProcessingJobRow.available_at.asc(),
                ProcessingJobRow.id.asc(),
            )
            .limit(1)
        )
        if stages:
            stmt = stmt.where(ProcessingJobRow.stage.in_([item.value for item in stages]))
        row = self.session.scalar(stmt)
        if row is None:
            return None
        row.status = "running"
        row.attempts += 1
        row.claimed_at = now
        row.error = None
        self.session.add(row)
        self.session.flush()
        return self._model(row)

    def complete(self, job_id: str) -> ProcessingJob:
        row = self._require(job_id)
        row.status = "completed"
        row.completed_at = datetime.now(UTC)
        row.error = None
        self.session.add(row)
        self.session.flush()
        return self._model(row)

    def fail(
        self,
        job_id: str,
        error: str,
        *,
        retry_delay_seconds: float = 30.0,
    ) -> ProcessingJob:
        row = self._require(job_id)
        row.error = error
        if row.attempts >= row.max_attempts:
            row.status = "failed"
            row.completed_at = datetime.now(UTC)
        else:
            row.status = "pending"
            row.claimed_at = None
            row.available_at = datetime.now(UTC) + timedelta(seconds=max(0.0, retry_delay_seconds))
        self.session.add(row)
        self.session.flush()
        return self._model(row)

    def requeue(self, job_id: str, *, reset_attempts: bool = False) -> ProcessingJob:
        row = self._require(job_id)
        row.status = "pending"
        row.available_at = datetime.now(UTC)
        row.claimed_at = None
        row.completed_at = None
        row.error = None
        if reset_attempts:
            row.attempts = 0
        self.session.add(row)
        self.session.flush()
        return self._model(row)

    def stats(self) -> QueueStats:
        statuses = {
            str(status): int(count)
            for status, count in self.session.execute(
                select(ProcessingJobRow.status, func.count()).group_by(ProcessingJobRow.status)
            )
        }
        stages = {
            str(stage): int(count)
            for stage, count in self.session.execute(
                select(ProcessingJobRow.stage, func.count()).group_by(ProcessingJobRow.stage)
            )
        }
        return QueueStats(
            pending=statuses.get("pending", 0),
            running=statuses.get("running", 0),
            completed=statuses.get("completed", 0),
            failed=statuses.get("failed", 0),
            by_stage=stages,
        )

    def _require(self, job_id: str) -> ProcessingJobRow:
        row = self.session.get(ProcessingJobRow, job_id)
        if row is None:
            raise KeyError(f"unknown processing job: {job_id}")
        return row

    @staticmethod
    def _model(row: ProcessingJobRow) -> ProcessingJob:
        return ProcessingJob(
            id=row.id,
            work_id=row.work_id,
            asset_id=row.asset_id,
            stage=ProcessingStage(row.stage),
            status=row.status,
            priority=row.priority,
            attempts=row.attempts,
            max_attempts=row.max_attempts,
            available_at=row.available_at,
            claimed_at=row.claimed_at,
            completed_at=row.completed_at,
            error=row.error,
            payload=row.payload_json,
        )
