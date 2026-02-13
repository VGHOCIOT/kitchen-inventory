from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from db.base import Base
import uuid

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    title = Column(String, nullable=False)
    instructions = Column(ARRAY(String), default=list)
    source_url = Column(String, nullable=True)