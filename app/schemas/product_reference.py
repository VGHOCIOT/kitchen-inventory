from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from models.product_reference import ProductType


class ProductReferenceOut(BaseModel):
    id: UUID
    product_type: ProductType
    barcode: Optional[str] = None  # Nullable for PLU items
    name: str
    brands: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    package_quantity: Optional[float] = None
    package_unit: Optional[str] = None
    meta_data: Optional[dict] = None

    class Config:
        from_attributes = True


class CreateFreshItemIn(BaseModel):
    """Schema for adding fresh/weight-based items (PLU) without barcode"""
    name: str
    weight_grams: float
    categories: Optional[list[str]] = None
    brands: Optional[list[str]] = None