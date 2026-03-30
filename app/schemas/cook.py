from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CookRequest(BaseModel):
    recipe_id: UUID
    substitutions: Optional[dict[str, str]] = None


class DeductedItem(BaseModel):
    ingredient: str
    amount: float
    unit: str


class SubstitutedItem(BaseModel):
    original: str
    substitute: str
    amount: float
    unit: str


class InsufficientItem(BaseModel):
    ingredient: str
    needed: float
    available: float
    unit: str


class CookResponse(BaseModel):
    recipe_title: str
    deducted: list[DeductedItem]
    substituted: list[SubstitutedItem]
    insufficient: list[InsufficientItem]
    unmapped: list[str]
