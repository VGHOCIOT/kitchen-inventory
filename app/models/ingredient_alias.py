from sqlalchemy import Column, Integer, String, ForeignKey, Date, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from db.base import Base

class IngredientAlias(Base):
    __tablename__ = "ingredient_aliases"
    id = Column(Integer, primary_key=True)
    alias = Column(String, index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredient_references.id", ondelete="CASCADE"))

    ingredient = relationship("IngredientReference", back_populates="aliases")
