from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from db.base import Base
import uuid

class IngredientAlias(Base):
    __tablename__ = "ingredient_aliases"
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    alias = Column(String, index=True, nullable=False)
    ingredient_id = Column(PGUUID(as_uuid=True), ForeignKey("ingredient_references.id", ondelete="CASCADE"))
