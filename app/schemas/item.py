from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from models.item import Locations


class ItemOut(BaseModel):
    id: UUID
    product_reference_id: UUID
    location: Locations
    qty: int
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanIn(BaseModel):
    barcode: str
    location: Locations = Locations.FRIDGE


class ScanOut(BaseModel):
    product_reference: "ProductReferenceOut"
    item: ItemOut
    data_quality_warning: Optional[str] = None  # Warning if product data is incomplete

    class Config:
        from_attributes = True


class AdjustQuantityIn(BaseModel):
    product_reference_id: UUID
    location: Locations
    delta: int


class MoveItemIn(BaseModel):
    product_reference_id: UUID
    from_location: Locations
    to_location: Locations
    quantity: int


class DeleteItemIn(BaseModel):
    product_reference_id: UUID
    location: Locations


# Import here to avoid circular dependency
from schemas.product_reference import ProductReferenceOut
ScanOut.model_rebuild()