from sqlalchemy import Column, Integer, String, ForeignKey, Date, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from db.base import Base

class IngredientReference(Base):
    __tablename__ = "ingredient_references"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    normalized_name = Column(String, index=True)
    meta_data = Column(JSON, nullable=True)

    aliases = relationship("IngredientAlias", back_populates="ingredient", cascade="all, delete") 
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")