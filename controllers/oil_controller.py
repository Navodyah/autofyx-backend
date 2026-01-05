from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.oil import OilQuality
from typing import Optional


async def create_oil_quality(db: AsyncSession, oil_grade: str, description: Optional[str] = None):
    """Create a new oil quality"""
    new_oil_quality = OilQuality(
        oil_grade=oil_grade,
        description=description
    )
    db.add(new_oil_quality)
    await db.commit()
    await db.refresh(new_oil_quality)
    return new_oil_quality


async def get_oil_quality_by_id(db: AsyncSession, oil_id: int):
    """Get an oil quality by ID"""
    result = await db.execute(select(OilQuality).filter(OilQuality.oil_id == oil_id))
    return result.scalar_one_or_none()


async def get_all_oil_qualities(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all oil qualities with pagination"""
    result = await db.execute(select(OilQuality).offset(skip).limit(limit))
    return result.scalars().all()


async def update_oil_quality(db: AsyncSession, oil_id: int, oil_grade: Optional[str] = None, description: Optional[str] = None):
    """Update an oil quality"""
    result = await db.execute(select(OilQuality).filter(OilQuality.oil_id == oil_id))
    oil_quality = result.scalar_one_or_none()
    if not oil_quality:
        return None

    if oil_grade is not None:
        oil_quality.oil_grade = oil_grade
    if description is not None:
        oil_quality.description = description

    await db.commit()
    await db.refresh(oil_quality)
    return oil_quality


async def delete_oil_quality(db: AsyncSession, oil_id: int):
    """Delete an oil quality"""
    result = await db.execute(select(OilQuality).filter(OilQuality.oil_id == oil_id))
    oil_quality = result.scalar_one_or_none()
    if not oil_quality:
        return False

    await db.delete(oil_quality)
    await db.commit()
    return True
