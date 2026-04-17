from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CookRequest(BaseModel):
    recipe_id: UUID
    substitutions: Optional[dict[UUID, UUID]] = None


class DeductedItem(BaseModel):
    ingredient: str
    amount: float
    unit: str


class CookResponse(BaseModel):
    recipe_title: str
    deducted: list[DeductedItem]
    failed: list[str]
