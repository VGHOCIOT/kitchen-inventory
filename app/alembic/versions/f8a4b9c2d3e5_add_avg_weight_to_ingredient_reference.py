"""add avg_weight to ingredient_reference

Revision ID: f8a4b9c2d3e5
Revises: e7f3c8d9a1b2
Create Date: 2026-02-15 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a4b9c2d3e5'
down_revision: Union[str, Sequence[str], None] = 'e7f3c8d9a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add average weight fields to ingredient_references for fresh ingredient matching."""
    # Add avg_weight_grams column
    op.add_column('ingredient_references',
                  sa.Column('avg_weight_grams', sa.Float(), nullable=True))

    # Add weight_source column
    op.add_column('ingredient_references',
                  sa.Column('weight_source', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove average weight fields from ingredient_references."""
    op.drop_column('ingredient_references', 'weight_source')
    op.drop_column('ingredient_references', 'avg_weight_grams')
