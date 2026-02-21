"""Merge multiple heads into one

Revision ID: e9f0a1b2c3d4
Revises: c3d4e5f6g7h8, d1e2f3a4b5c6
Create Date: 2026-02-20 00:00:00.000000

"""
from typing import Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e9f0a1b2c3d4'
down_revision: Union[str, tuple] = ('c3d4e5f6g7h8', 'd1e2f3a4b5c6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
