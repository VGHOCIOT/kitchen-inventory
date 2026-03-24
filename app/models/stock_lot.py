from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid

from db.base import Base
from models.item import Locations


class StockLot(Base):
    __tablename__ = "stock_lots"

    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    product_reference_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("product_references.id"),
        nullable=False,
        index=True,
    )
    location = Column(SAEnum(Locations), nullable=False)
    initial_quantity = Column(Float, nullable=False)
    remaining_quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)  # "g", "ml", or "unit"
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
