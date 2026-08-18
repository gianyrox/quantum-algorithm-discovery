from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.storage.models import ResearchObjectRelationRow


class ResearchObjectRelation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_type: str
    subject_id: str
    relation_type: str
    object_type: str
    object_id: str
    provider: str
    native_relation_type: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, object] = Field(default_factory=dict)


class ResearchObjectRelationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, relation: ResearchObjectRelation) -> ResearchObjectRelationRow:
        row = self.session.scalar(
            select(ResearchObjectRelationRow).where(
                ResearchObjectRelationRow.subject_type == relation.subject_type,
                ResearchObjectRelationRow.subject_id == relation.subject_id,
                ResearchObjectRelationRow.relation_type == relation.relation_type,
                ResearchObjectRelationRow.object_type == relation.object_type,
                ResearchObjectRelationRow.object_id == relation.object_id,
                ResearchObjectRelationRow.provider == relation.provider,
            )
        )
        if row is None:
            row = ResearchObjectRelationRow(
                subject_type=relation.subject_type,
                subject_id=relation.subject_id,
                relation_type=relation.relation_type,
                native_relation_type=relation.native_relation_type,
                object_type=relation.object_type,
                object_id=relation.object_id,
                provider=relation.provider,
                retrieved_at=relation.retrieved_at,
                payload_json=relation.payload,
            )
        else:
            row.native_relation_type = relation.native_relation_type
            row.retrieved_at = relation.retrieved_at
            row.payload_json = relation.payload
        self.session.add(row)
        self.session.flush()
        return row
