from discovery.review.schema import ReviewDecision
from discovery.review.service import ReviewService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_review_event_is_persisted(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'review.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        event = ReviewService(session).record(
            object_type="problem",
            object_id="p",
            reviewer_id="human-1",
            decision=ReviewDecision.REVISE,
        )
        assert event.decision == ReviewDecision.REVISE
