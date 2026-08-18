from __future__ import annotations

from sqlalchemy.orm import Session

from discovery.corpus.schema import Work
from discovery.storage.repositories import WorkRepository


class CorpusService:
    def __init__(self, session: Session) -> None:
        self.works = WorkRepository(session)

    def ingest(self, works: list[Work]) -> list[str]:
        return [self.works.upsert(work).id for work in works]
