from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from enum import Enum
import uuid
from db.base import Base

class Locations(str, Enum):
    FRIDGE = "Fridge"
    FREEZER = "Freezer"
    CUPBOARD = "Cupboard"

class Item(Base):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint('product_reference_id', 'location', name='_product_location_uc'),)
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    product_reference_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("product_references.id"),
        nullable=True
    )
    location = Column(SAEnum(Locations), default=Locations.FRIDGE)
    qty = Column(Integer, default=1)
    expires_at = Column(DateTime, nullable=True)
