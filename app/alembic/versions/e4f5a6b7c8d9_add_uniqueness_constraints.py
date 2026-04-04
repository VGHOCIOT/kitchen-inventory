"""add uniqueness constraints for aliases, substitutions, recipe source_url, and recipe_ingredients

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ingredient_aliases.alias — was index=True only, now unique
    op.drop_index('ix_ingredient_aliases_alias', table_name='ingredient_aliases')
    op.create_index(
        'ix_ingredient_aliases_alias',
        'ingredient_aliases',
        ['alias'],
        unique=True,
    )

    # ingredient_substitutions — composite unique on (original_id, substitute_id)
    op.create_unique_constraint(
        '_substitution_pair_uc',
        'ingredient_substitutions',
        ['original_ingredient_id', 'substitute_ingredient_id'],
    )

    # recipes.source_url — partial unique index (NULLs excluded)
    op.create_index(
        'ix_recipes_source_url_unique',
        'recipes',
        ['source_url'],
        unique=True,
        postgresql_where='source_url IS NOT NULL',
    )

    # recipe_ingredients — composite unique on (recipe_id, ingredient_text)
    op.create_unique_constraint(
        '_recipe_ingredient_text_uc',
        'recipe_ingredients',
        ['recipe_id', 'ingredient_text'],
    )


def downgrade() -> None:
    op.drop_constraint('_recipe_ingredient_text_uc', 'recipe_ingredients', type_='unique')
    op.drop_index('ix_recipes_source_url_unique', table_name='recipes')
    op.drop_constraint('_substitution_pair_uc', 'ingredient_substitutions', type_='unique')
    op.drop_index('ix_ingredient_aliases_alias', table_name='ingredient_aliases')
    op.create_index('ix_ingredient_aliases_alias', 'ingredient_aliases', ['alias'], unique=False)
