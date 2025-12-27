from sqlalchemy import Column, Integer, String, Date, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    instructions = Column(ARRAY(String), default=list)
    source_url = Column(String, nullable=True)

    ingredients = relationship(
        "RecipeIngredient",
        back_populates = "recipe",
        cascade = "all, delete-orphan"
    )