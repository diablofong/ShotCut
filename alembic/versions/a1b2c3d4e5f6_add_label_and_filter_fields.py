"""add mark label and highlight filter_players/filter_categories

Revision ID: a1b2c3d4e5f6
Revises: c8abb19185e5
Create Date: 2026-02-17 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c8abb19185e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('marks', sa.Column('label', sa.String(200), nullable=False, server_default=''))
    op.add_column('highlights', sa.Column('filter_players', sa.Text(), nullable=True))
    op.add_column('highlights', sa.Column('filter_categories', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('highlights', 'filter_categories')
    op.drop_column('highlights', 'filter_players')
    op.drop_column('marks', 'label')
