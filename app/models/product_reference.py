from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from db.base import Base
import uuid

class ProductReference(Base):
    __tablename__ = "product_references"
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True, nullable=False)
    categories = Column(ARRAY(String), nullable=True)
    brands = Column(ARRAY(String), nullable=True)
    meta_data = Column(JSON, nullable=True)
