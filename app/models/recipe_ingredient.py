from sqlalchemy import Column, Integer, String, ForeignKey, Date, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(
                    Integer, 
                    ForeignKey("recipes.id", ondelete="CASCADE"),
                    nullable=False       
                )
    ingredient_text = Column(String, nullable=False)
    canonical_ingredient_id = Column(
                                Integer,
                                ForeignKey("ingredient_references.id"),
                                nullable=False
                              )
    quantity = Column(Integer, default=1)
    unit = Column(String, default='g')

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("IngredientReference", back_populates="recipe_ingredients")