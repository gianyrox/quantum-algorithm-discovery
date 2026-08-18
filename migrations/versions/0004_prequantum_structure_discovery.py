"""Pre-quantum structure discovery, coverage feedback, and reproducibility.

Revision ID: 0004
Revises: 0003
"""
from __future__ import annotations

from alembic import op

import discovery.storage.models  # noqa: F401
from discovery.storage.base import Base

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

_NEW_TABLES = (
    "document_intelligence",
    "problem_quality",
    "math_fingerprint",
    "structural_similarity",
    "cross_domain_relation",
    "discovery_iteration",
    "retrieval_feedback",
    "research_manifest",
)


def upgrade() -> None:
    bind = op.get_bind()
    for name in _NEW_TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_NEW_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
