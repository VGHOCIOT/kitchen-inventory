from sqlalchemy import Column, String, JSON, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from db.base import Base
import uuid
import enum

class ProductType(str, enum.Enum):
    """Product type: UPC (barcode) or PLU (fresh/weight-based)"""
    UPC = "upc"  # Packaged products with barcodes
    PLU = "plu"  # Fresh items identified by PLU code or manual entry

class ProductReference(Base):
    __tablename__ = "product_references"
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    product_type = Column(SQLEnum(ProductType), nullable=False, default=ProductType.UPC, index=True)
    barcode = Column(String, unique=True, index=True, nullable=True)  # Nullable for PLU items
    name = Column(String, index=True, nullable=False)
    categories = Column(ARRAY(String), nullable=True)
    brands = Column(ARRAY(String), nullable=True)
    package_quantity = Column(Float, nullable=True)
    package_unit = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)
