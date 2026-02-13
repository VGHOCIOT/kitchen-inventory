from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class ProductReferenceOut(BaseModel):
    id: UUID
    barcode: str
    name: str
    brands: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    package_quantity: Optional[float] = None
    package_unit: Optional[str] = None
    meta_data: Optional[dict] = None

    class Config:
        from_attributes = True