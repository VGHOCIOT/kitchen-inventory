from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.models.item import Item
from app.api.services.openfood import lookup_barcode
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_or_create_from_barcode(barcode: str, location: str = "fridge") -> Item:
    """
    Get an existing item by barcode or create a new one if it doesn't exist.
    If creating a new item, fetch product information from OpenFoodFacts API.
    """
    db: Session = next(get_db())
    
    try:
        # First, try to find existing item by barcode
        stmt = select(Item).where(Item.barcode == barcode)
        existing_item = db.execute(stmt).scalar_one_or_none()
        
        if existing_item:
            # Update location if different
            if existing_item.location != location:
                existing_item.location = location
                db.commit()
                db.refresh(existing_item)
            return existing_item
        
        # Item doesn't exist, create new one
        # First get product info from OpenFoodFacts
        product_info = await lookup_barcode(barcode)
        
        if not product_info:
            # Fallback if API fails
            product_info = {
                "name": f"Unknown Product {barcode}",
                "brand": None,
                "category": None,
                "image_url": None
            }
        
        # Create new item
        new_item = Item(
            barcode=barcode,
            name=product_info.get("name", f"Unknown Product {barcode}"),
            brand=product_info.get("brand"),
            category=product_info.get("category"),
            location=location,
            image_url=product_info.get("image_url")
        )
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        logger.info(f"Created new item: {new_item.name} (barcode: {barcode})")
        return new_item
        
    except Exception as e:
        logger.error(f"Error in get_or_create_from_barcode: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_item_by_id(item_id: int) -> Optional[Item]:
    """Get an item by its ID."""
    db: Session = next(get_db())
    
    try:
        stmt = select(Item).where(Item.id == item_id)
        return db.execute(stmt).scalar_one_or_none()
    finally:
        db.close()

async def get_item_by_barcode(barcode: str) -> Optional[Item]:
    """Get an item by its barcode."""
    db: Session = next(get_db())
    
    try:
        stmt = select(Item).where(Item.barcode == barcode)
        return db.execute(stmt).scalar_one_or_none()
    finally:
        db.close()

async def get_items_by_location(location: str) -> list[Item]:
    """Get all items in a specific location."""
    db: Session = next(get_db())
    
    try:
        stmt = select(Item).where(Item.location == location)
        result = db.execute(stmt)
        return result.scalars().all()
    finally:
        db.close()

async def update_item_location(item_id: int, new_location: str) -> Optional[Item]:
    """Update an item's location."""
    db: Session = next(get_db())
    
    try:
        stmt = select(Item).where(Item.id == item_id)
        item = db.execute(stmt).scalar_one_or_none()
        
        if item:
            item.location = new_location
            db.commit()
            db.refresh(item)
        
        return item
    except Exception as e:
        logger.error(f"Error updating item location: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def delete_item(item_id: int) -> bool:
    """Delete an item by its ID."""
    db: Session = next(get_db())
    
    try:
        stmt = select(Item).where(Item.id == item_id)
        item = db.execute(stmt).scalar_one_or_none()
        
        if item:
            db.delete(item)
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_all_items() -> list[Item]:
    """Get all items in the inventory."""
    db: Session = next(get_db())
    
    try:
        stmt = select(Item)
        result = db.execute(stmt)
        return result.scalars().all()
    finally:
        db.close()