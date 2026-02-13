from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from db.base import Base
import uuid

class IngredientReference(Base):
    __tablename__ = "ingredient_references"
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    normalized_name = Column(String, index=True)
    meta_data = Column(JSON, nullable=True)