from sqlalchemy import Column, String, ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from db.base import Base
import uuid

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint('recipe_id', 'ingredient_text', name='_recipe_ingredient_text_uc'),
    )
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    recipe_id = Column(PGUUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    ingredient_text = Column(String, nullable=False)
    canonical_ingredient_id = Column(PGUUID(as_uuid=True), ForeignKey("ingredient_references.id"), nullable=False)
    quantity = Column(Float, default=1.0)
    unit = Column(String, default='g')