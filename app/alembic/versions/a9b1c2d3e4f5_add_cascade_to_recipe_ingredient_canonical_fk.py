"""add cascade to recipe_ingredient canonical_ingredient_id fk

Revision ID: a9b1c2d3e4f5
Revises: f8a4b9c2d3e5
Create Date: 2026-04-17

"""
from alembic import op

revision = 'a9b1c2d3e4f5'
down_revision = 'f8a4b9c2d3e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('recipe_ingredients_canonical_ingredient_id_fkey', 'recipe_ingredients', type_='foreignkey')
    op.create_foreign_key(
        'recipe_ingredients_canonical_ingredient_id_fkey',
        'recipe_ingredients', 'ingredient_references',
        ['canonical_ingredient_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('recipe_ingredients_canonical_ingredient_id_fkey', 'recipe_ingredients', type_='foreignkey')
    op.create_foreign_key(
        'recipe_ingredients_canonical_ingredient_id_fkey',
        'recipe_ingredients', 'ingredient_references',
        ['canonical_ingredient_id'], ['id'],
    )
