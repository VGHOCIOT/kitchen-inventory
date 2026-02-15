"""add product_type plu_upc distinction

Revision ID: e7f3c8d9a1b2
Revises: d36a07b2efef
Create Date: 2026-02-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f3c8d9a1b2'
down_revision: Union[str, Sequence[str], None] = 'd36a07b2efef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add product_type column to distinguish UPC (barcode) vs PLU (fresh/weight) items."""
    # Create enum type
    product_type_enum = sa.Enum('upc', 'plu', name='producttype')
    product_type_enum.create(op.get_bind(), checkfirst=True)

    # Add product_type column with default 'upc' for existing rows
    op.add_column('product_references',
                  sa.Column('product_type', product_type_enum, nullable=False, server_default='upc'))

    # Create index on product_type
    op.create_index(op.f('ix_product_references_product_type'), 'product_references', ['product_type'], unique=False)

    # Make barcode nullable (PLU items won't have barcodes)
    # This is already nullable in the initial migration, so no change needed


def downgrade() -> None:
    """Remove product_type column."""
    op.drop_index(op.f('ix_product_references_product_type'), table_name='product_references')
    op.drop_column('product_references', 'product_type')

    # Drop enum type
    product_type_enum = sa.Enum('upc', 'plu', name='producttype')
    product_type_enum.drop(op.get_bind(), checkfirst=True)
