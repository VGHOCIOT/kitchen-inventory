from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from crud.items import get_or_create_from_barcode

router = APIRouter()

class ScanIn(BaseModel):
    barcode: str
    location: str = "fridge"

@router.post("/scan")
async def scan_item(payload: ScanIn, db: AsyncSession = Depends(get_db)):
    return await get_or_create_from_barcode(payload.barcode, payload.location, db)