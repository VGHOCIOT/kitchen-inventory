from sqlalchemy.ext.declarative import declarative_base

# Create the base class for all SQLAlchemy models
Base = declarative_base()

# Import all models here to ensure they are registered with Base
# This is important for Alembic to detect all tables
# from models.item import Item  # noqa: E402

# Export the metadata for Alembic
metadata = Base.metadata