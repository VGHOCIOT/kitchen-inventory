from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from crud.items import (
    scan_barcode,
    get_all_items,
    get_items_by_location,
    move_item,
    adjust_item_quantity,
    delete_item
)
from schemas.item import ItemOut

router = APIRouter()

class ScanIn(BaseModel):
    barcode: str
    location: str = "fridge"

@router.post("/scan", response_model=ItemOut)
async def scan_item(payload: ScanIn, db: AsyncSession = Depends(get_db)):
    return await scan_barcode(db, payload.barcode, payload.location)

@router.get("/", response_model= list[ItemOut])
async def list_items(db: AsyncSession = Depends(get_db)):
    return await get_all_items(db)

@router.get("/location/{location}", response_model=list[ItemOut])
async def list_items_by_location(location: str, db: AsyncSession = Depends(get_db)):
    return await get_items_by_location(location, db)

@router.patch("/{item_id}/move", response_mode=ItemOut)
async def move_item_endpoint(item_id: int, location: str, db: AsyncSession = Depends(get_db)):
    item =  await move_item(item_id, location, db)

    if not item: 
        raise HTTPException(404, "Item not found")
    return item

@router.patch("/{item_id}/quantity", response_model= ItemOut | None)
async def adjust_quantity(item_id: int, delta: int, db: AsyncSession = Depends(get_db)):
    return await adjust_item_quantity(item_id, delta, db)

@router.delete("/{item_id}", status_code=204)
async def delete_item_endpoint(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await delete_item(item_id, db)

    if not item:
        raise HTTPException(404, "Item not found")
