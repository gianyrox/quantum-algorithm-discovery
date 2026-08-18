"""Gateway-first feed402 acquisition provenance.

Revision ID: 0005
Revises: 0004
"""
from __future__ import annotations

from alembic import op

import discovery.storage.models  # noqa: F401
from discovery.storage.base import Base

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["feed402_envelope"].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["feed402_envelope"].drop(bind=bind, checkfirst=True)
