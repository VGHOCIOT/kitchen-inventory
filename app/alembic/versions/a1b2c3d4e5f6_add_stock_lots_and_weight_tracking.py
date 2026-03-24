"""add stock_lots table and convert items to weight-based tracking

Revision ID: a1b2c3d4e5f6
Revises: f8a4b9c2d3e5
Create Date: 2026-03-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a4b9c2d3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create stock_lots table
    op.create_table(
        'stock_lots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('product_reference_id', UUID(as_uuid=True),
                   sa.ForeignKey('product_references.id'), nullable=False),
        sa.Column('location', sa.Enum('Fridge', 'Freezer', 'Cupboard', name='locations',
                                       create_type=False), nullable=False),
        sa.Column('initial_quantity', sa.Float(), nullable=False),
        sa.Column('remaining_quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_stock_lots_id', 'stock_lots', ['id'])
    op.create_index('ix_stock_lots_product_reference_id', 'stock_lots', ['product_reference_id'])

    # 2. Add unit column to items (before altering qty, so we can set it during data migration)
    op.add_column('items', sa.Column('unit', sa.String(), nullable=True))

    # 3. Data migration: convert existing items from package count to weight
    #    For each item: qty_new = qty_old * product.package_quantity (or keep as count)
    #    Also create a StockLot for each existing item
    conn = op.get_bind()
    items = conn.execute(sa.text("""
        SELECT i.id, i.product_reference_id, i.location, i.qty,
               p.package_quantity, p.package_unit
        FROM items i
        JOIN product_references p ON i.product_reference_id = p.id
    """)).fetchall()

    for item in items:
        item_id, prod_ref_id, location, qty, pkg_qty, pkg_unit = item

        if pkg_qty is not None and pkg_unit is not None:
            total_weight = qty * pkg_qty
            unit = pkg_unit
        else:
            total_weight = float(qty)
            unit = 'unit'

        # Update the item to weight-based qty and set unit
        conn.execute(sa.text("""
            UPDATE items SET qty = :weight, unit = :unit WHERE id = :id
        """), {"weight": total_weight, "unit": unit, "id": item_id})

        # Create a StockLot for the existing inventory
        import uuid
        conn.execute(sa.text("""
            INSERT INTO stock_lots (id, product_reference_id, location,
                                    initial_quantity, remaining_quantity, unit, created_at)
            VALUES (:id, :prod_ref_id, :location, :qty, :qty, :unit, NOW())
        """), {
            "id": str(uuid.uuid4()),
            "prod_ref_id": prod_ref_id,
            "location": location,
            "qty": total_weight,
            "unit": unit,
        })

    # 4. Alter items.qty from Integer to Float
    op.alter_column('items', 'qty',
                     type_=sa.Float(),
                     existing_type=sa.Integer(),
                     existing_nullable=False)

    # 5. Make unit non-nullable now that all rows have values
    op.alter_column('items', 'unit', nullable=False)


def downgrade() -> None:
    # Revert items.qty to Integer
    op.alter_column('items', 'qty',
                     type_=sa.Integer(),
                     existing_type=sa.Float(),
                     existing_nullable=False)

    # Remove unit column
    op.drop_column('items', 'unit')

    # Drop stock_lots
    op.drop_index('ix_stock_lots_product_reference_id', 'stock_lots')
    op.drop_index('ix_stock_lots_id', 'stock_lots')
    op.drop_table('stock_lots')
