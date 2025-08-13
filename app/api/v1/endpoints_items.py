from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.crud.items import get_or_create_from_barcode

router = APIRouter()

class ScanIn(BaseModel):
    barcode: str
    location: str = "fridge"

@router.post("/scan")
async def scan_item(payload: ScanIn):
    item = await get_or_create_from_barcode(payload.barcode, payload.location)
    return item