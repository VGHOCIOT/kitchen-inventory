"""add cascade delete to item and stock_lot foreign keys

Revision ID: d3e4f5a6b7c8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Items: drop old FK, add with CASCADE
    op.drop_constraint('items_product_reference_id_fkey', 'items', type_='foreignkey')
    op.create_foreign_key(
        'items_product_reference_id_fkey', 'items',
        'product_references', ['product_reference_id'], ['id'],
        ondelete='CASCADE',
    )

    # StockLots: drop old FK, add with CASCADE
    op.drop_constraint('stock_lots_product_reference_id_fkey', 'stock_lots', type_='foreignkey')
    op.create_foreign_key(
        'stock_lots_product_reference_id_fkey', 'stock_lots',
        'product_references', ['product_reference_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('stock_lots_product_reference_id_fkey', 'stock_lots', type_='foreignkey')
    op.create_foreign_key(
        'stock_lots_product_reference_id_fkey', 'stock_lots',
        'product_references', ['product_reference_id'], ['id'],
    )

    op.drop_constraint('items_product_reference_id_fkey', 'items', type_='foreignkey')
    op.create_foreign_key(
        'items_product_reference_id_fkey', 'items',
        'product_references', ['product_reference_id'], ['id'],
    )
