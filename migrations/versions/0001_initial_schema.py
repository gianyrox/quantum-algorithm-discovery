"""Initial scientific-discovery canonical schema.

Revision ID: 0001
Revises: none
"""
from __future__ import annotations

from alembic import op

import discovery.storage.models  # noqa: F401
from discovery.storage.base import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
