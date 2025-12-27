import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# -----------------------------
# Alembic Config
# -----------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------
# Make app importable
# -----------------------------
sys.path.append(os.path.abspath(os.getcwd()))

# -----------------------------
# Import Base + models
# -----------------------------
from db.base import Base

# Import all models - this ensures Alembic can detect them
# If you have __init__.py importing all models, just import from there:
import models  # This will trigger all the imports in models/__init__.py

# OR import each model explicitly:
# from models.recipe import Recipe
# from models.recipe_ingredient import RecipeIngredient
# from models.ingredient_reference import IngredientReference
# from models.ingredient_alias import IngredientAlias
# from models.product_reference import ProductReference
# from models.item import Item

target_metadata = Base.metadata

# -----------------------------
# Database URL
# -----------------------------
def get_database_url():
    """Build sync database URL for Alembic"""
    return (
        f"postgresql+psycopg2://" 
        f"{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('DB_HOST', 'db')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )

config.set_main_option("sqlalchemy.url", get_database_url())

# -----------------------------
# Offline migrations
# -----------------------------
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

# -----------------------------
# Online migrations
# -----------------------------
def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# -----------------------------
# Entrypoint
# -----------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()