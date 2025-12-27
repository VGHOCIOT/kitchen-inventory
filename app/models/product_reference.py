from sqlalchemy import Column, Integer, String, ForeignKey, Date, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductReference(Base):
    __tablename__ = "product_references"
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)