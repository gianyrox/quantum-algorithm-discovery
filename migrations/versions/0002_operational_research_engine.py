"""Operational research engine tables.

Revision ID: 0002
Revises: 0001
"""
from __future__ import annotations

from alembic import op

import discovery.storage.models  # noqa: F401
from discovery.storage.base import Base

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_NEW_TABLES = (
    "research_object_relation",
    "retrieval_query",
    "harvest_checkpoint",
    "document_parse_run",
    "problem_extraction_run",
    "review_event",
    "unknown_vocabulary_candidate",
    "coverage_snapshot",
    "quantum_screening_run",
    "algorithm_proposal",
    "proposal_evaluation",
)


def upgrade() -> None:
    bind = op.get_bind()
    for name in _NEW_TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_NEW_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
