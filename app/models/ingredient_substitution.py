from sqlalchemy import Column, String, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from db.base import Base
import uuid

class IngredientSubstitution(Base):
    """Defines ingredient substitution rules"""
    __tablename__ = "ingredient_substitutions"

    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)

    # What ingredient can be substituted
    original_ingredient_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("ingredient_references.id", ondelete="CASCADE"),
        nullable=False
    )

    # What to use instead
    substitute_ingredient_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("ingredient_references.id", ondelete="CASCADE"),
        nullable=False
    )

    # Conversion ratio (1.0 = same amount, 1.5 = use 50% more substitute)
    ratio = Column(Float, default=1.0, nullable=False)

    # Optional: quality/preference score (1-10, how good is this substitution?)
    quality_score = Column(Integer, default=5, nullable=True)

    # Optional: notes like "works better for baking than frying"
    notes = Column(String, nullable=True)
