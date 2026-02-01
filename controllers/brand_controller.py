from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.brand import Brand
from typing import Optional


async def create_brand(db: AsyncSession, brand_name: str, country: Optional[str] = None):
    """Create a new brand"""
    new_brand = Brand(brand_name=brand_name, country=country)
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    if new_brand.brand_id is None:
        await db.rollback()
        raise ValueError("Failed to generate brand_id")
    return new_brand




async def get_brand_by_id(db: AsyncSession, brand_id: int):
    """Get a brand by ID"""
    result = await db.execute(select(Brand).filter(Brand.brand_id == brand_id))
    return result.scalar_one_or_none()


async def get_all_brands(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all brands with pagination"""
    result = await db.execute(select(Brand).offset(skip).limit(limit))
    return result.scalars().all()


async def update_brand(db: AsyncSession, brand_id: int, brand_name: Optional[str] = None, country: Optional[str] = None):
    """Update a brand"""
    result = await db.execute(select(Brand).filter(Brand.brand_id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        return None

    if brand_name is not None:
        brand.brand_name = brand_name
    if country is not None:
        brand.country = country

    await db.commit()
    await db.refresh(brand)
    return brand


async def delete_brand(db: AsyncSession, brand_id: int):
    """Delete a brand"""
    result = await db.execute(select(Brand).filter(Brand.brand_id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        return False

    await db.delete(brand)
    await db.commit()
    return True
