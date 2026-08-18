from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from discovery.storage.models import ConceptRow, DisciplineRow, TermRow


def ontology_stats(session: Session) -> dict[str, int]:
    return {
        "disciplines": int(session.scalar(select(func.count()).select_from(DisciplineRow)) or 0),
        "concepts": int(session.scalar(select(func.count()).select_from(ConceptRow)) or 0),
        "terms": int(session.scalar(select(func.count()).select_from(TermRow)) or 0),
    }
