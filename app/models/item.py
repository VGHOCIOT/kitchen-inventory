from sqlalchemy import Column, Integer, String, Date, JSON
from app.db.base import Base

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, index=True, nullable=False)
    name = Column(String, nullable=True)
    location = Column(String, default="fridge")
    qty = Column(Integer, default=1)
    product_data = Column(JSON, default={})
    expiry = Column(Date, nullable=True)