"""Real-data execution, request audit, identity, integrity, and durable jobs.

Revision ID: 0003
Revises: 0002
"""
from __future__ import annotations

from alembic import op

import discovery.storage.models  # noqa: F401
from discovery.storage.base import Base

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_NEW_TABLES = (
    "provider_request",
    "identity_assertion",
    "integrity_assertion",
    "provider_snapshot",
    "research_campaign",
    "campaign_run",
    "processing_job",
    "provider_harvest_checkpoint",
    "asset_acquisition",
)


def upgrade() -> None:
    bind = op.get_bind()
    for name in _NEW_TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_NEW_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
