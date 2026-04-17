from pydantic import BaseModel, Field
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


class ItemOut(BaseModel):
    id: UUID
    product_reference_id: UUID
    location: Locations
    qty: float
    unit: str
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanIn(BaseModel):
    barcode: str = Field(..., min_length=1, max_length=20, pattern=r"^\d+$")
    location: Locations = Locations.FRIDGE


class ScanOut(BaseModel):
    product_reference: "ProductReferenceOut"
    item: ItemOut
    data_quality_warning: Optional[str] = None

    class Config:
        from_attributes = True


class AdjustQuantityIn(BaseModel):
    product_reference_id: UUID
    location: Locations
    delta: float


class MoveItemIn(BaseModel):
    product_reference_id: UUID
    from_location: Locations
    to_location: Locations
    quantity: float


class DeleteItemIn(BaseModel):
    product_reference_id: UUID
    location: Locations


# Import here to avoid circular dependency
from schemas.product_reference import ProductReferenceOut
ScanOut.model_rebuild()


class ItemWithProductOut(BaseModel):
    item: ItemOut
    product: ProductReferenceOut

    class Config:
        from_attributes = True
