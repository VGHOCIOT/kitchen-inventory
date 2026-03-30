from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.shopping_list import ShoppingListRequest, ShoppingListResponse
from api.services.shopping_list_service import generate_shopping_list

router = APIRouter(tags=["Shopping List"])


@router.post("/from-recipes", response_model=ShoppingListResponse)
async def shopping_list_from_recipes(
    payload: ShoppingListRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a shopping list from selected recipes.

    Consolidates all ingredient requirements across the given recipes,
    subtracts what's already in inventory, and returns what needs to be bought.
    """
    if not payload.recipe_ids:
        raise HTTPException(status_code=400, detail="At least one recipe_id is required")

    return await generate_shopping_list(db, payload.recipe_ids)
