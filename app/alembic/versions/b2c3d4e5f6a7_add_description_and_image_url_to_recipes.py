"""add description and image_url to recipes

Revision ID: b2c3d4e5f6a7
Revises: c4d5e6f7a8b9
Create Date: 2026-03-31 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recipes', sa.Column('description', sa.String(), nullable=True))
    op.add_column('recipes', sa.Column('image_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('recipes', 'image_url')
    op.drop_column('recipes', 'description')
