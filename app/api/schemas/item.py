from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class ItemOut(BaseModel):
    id: int
    barcode: str
    name: Optional[str]
    location: str
    qty: int
    brands: List[str]
    categories: List[str]
    expiry: Optional[date]

    class Config:
        from_attributes = True  # SQLAlchemy -> Pydantic