"""lowercase locations enum values

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f6
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL doesn't allow removing enum values, so we create a new type,
    # migrate the data, drop the old type, and rename.

    op.execute("CREATE TYPE locations_new AS ENUM ('fridge', 'freezer', 'cupboard')")

    op.execute("""
        ALTER TABLE items
        ALTER COLUMN location TYPE locations_new
        USING LOWER(location::text)::locations_new
    """)

    op.execute("""
        ALTER TABLE stock_lots
        ALTER COLUMN location TYPE locations_new
        USING LOWER(location::text)::locations_new
    """)

    op.execute("DROP TYPE locations")
    op.execute("ALTER TYPE locations_new RENAME TO locations")


def downgrade() -> None:
    op.execute("CREATE TYPE locations_old AS ENUM ('Fridge', 'Freezer', 'Cupboard')")

    op.execute("""
        ALTER TABLE items
        ALTER COLUMN location TYPE locations_old
        USING INITCAP(location::text)::locations_old
    """)

    op.execute("""
        ALTER TABLE stock_lots
        ALTER COLUMN location TYPE locations_old
        USING INITCAP(location::text)::locations_old
    """)

    op.execute("DROP TYPE locations")
    op.execute("ALTER TYPE locations_old RENAME TO locations")
