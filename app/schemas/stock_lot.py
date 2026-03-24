from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from models.item import Locations


class StockLotOut(BaseModel):
    id: UUID
    product_reference_id: UUID
    location: Locations
    initial_quantity: float
    remaining_quantity: float
    unit: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
