from __future__ import annotations

from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.review.schema import ReviewDecision, ReviewEvent
from discovery.storage.models import ReviewEventRow


class ReviewService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        object_type: str,
        object_id: str,
        reviewer_id: str,
        decision: ReviewDecision,
        notes: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> ReviewEvent:
        event_id = stable_id(
            "review-event",
            f"{object_type}:{object_id}:{reviewer_id}:{decision.value}:{notes or ''}",
        )
        event = ReviewEvent(
            id=event_id,
            object_type=object_type,
            object_id=object_id,
            reviewer_id=reviewer_id,
            decision=decision,
            notes=notes,
            payload=payload or {},
        )
        row = ReviewEventRow(
            id=event.id,
            object_type=event.object_type,
            object_id=event.object_id,
            reviewer_id=event.reviewer_id,
            decision=event.decision.value,
            created_at=event.created_at,
            notes=event.notes,
            payload_json=event.payload,
        )
        self.session.merge(row)
        self.session.flush()
        return event
