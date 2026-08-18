from __future__ import annotations

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.execution.queue import ProcessingQueue
from discovery.execution.schema import ProcessingStage
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.repositories import WorkRepository


def test_processing_queue_is_idempotent_and_retryable(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'queue.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        work_id = WorkRepository(session).upsert(
            Work.from_primary_identifier(
                scheme=IdentifierScheme.DOI,
                value="10.1000/queue",
                title="Queue",
            )
        ).id
        queue = ProcessingQueue(session)
        first = queue.enqueue(work_id=work_id, stage=ProcessingStage.ASSET_DISCOVERY)
        second = queue.enqueue(work_id=work_id, stage=ProcessingStage.ASSET_DISCOVERY)
        assert first.id == second.id
        claimed = queue.claim_next()
        assert claimed is not None
        assert claimed.status == "running"
        assert claimed.attempts == 1
        retried = queue.fail(claimed.id, "temporary", retry_delay_seconds=0)
        assert retried.status == "pending"
        claimed_again = queue.claim_next()
        assert claimed_again is not None
        assert claimed_again.attempts == 2
        completed = queue.complete(claimed_again.id)
        assert completed.status == "completed"
        assert queue.stats().completed == 1
