"""add opened_at to stock_lots

Revision ID: a1b2c3d4e5f6
Revises: f8a4b9c2d3e5
Create Date: 2026-05-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a4b9c2d3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stock_lots', sa.Column('opened_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('stock_lots', 'opened_at')
