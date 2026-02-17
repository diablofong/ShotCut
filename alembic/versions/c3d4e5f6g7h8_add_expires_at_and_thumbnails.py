"""add expires_at to share_links and thumbnail_path to videos/clips/highlights

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-17 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('share_links', sa.Column('expires_at', sa.DateTime(), nullable=True))
    op.add_column('videos', sa.Column('thumbnail_path', sa.String(1000), nullable=True))
    op.add_column('clips', sa.Column('thumbnail_path', sa.String(1000), nullable=True))
    op.add_column('highlights', sa.Column('thumbnail_path', sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column('highlights', 'thumbnail_path')
    op.drop_column('clips', 'thumbnail_path')
    op.drop_column('videos', 'thumbnail_path')
    op.drop_column('share_links', 'expires_at')
