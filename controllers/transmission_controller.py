from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.transmission import Transmission
from typing import Optional


async def create_transmission(db: AsyncSession, transmission_name: str, category: Optional[str] = None):
    """Create a new transmission"""
    new_transmission = Transmission(
        transmission_name=transmission_name,
        category=category
    )
    db.add(new_transmission)
    await db.commit()
    await db.refresh(new_transmission)
    return new_transmission


async def get_transmission_by_id(db: AsyncSession, transmission_id: int):
    """Get a transmission by ID"""
    result = await db.execute(select(Transmission).filter(Transmission.transmission_id == transmission_id))
    return result.scalar_one_or_none()


async def get_all_transmissions(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all transmissions with pagination"""
    result = await db.execute(select(Transmission).offset(skip).limit(limit))
    return result.scalars().all()


async def update_transmission(db: AsyncSession, transmission_id: int, transmission_name: Optional[str] = None, category: Optional[str] = None):
    """Update a transmission"""
    result = await db.execute(select(Transmission).filter(Transmission.transmission_id == transmission_id))
    transmission = result.scalar_one_or_none()
    if not transmission:
        return None

    if transmission_name is not None:
        transmission.transmission_name = transmission_name
    if category is not None:
        transmission.category = category

    await db.commit()
    await db.refresh(transmission)
    return transmission


async def delete_transmission(db: AsyncSession, transmission_id: int):
    """Delete a transmission"""
    result = await db.execute(select(Transmission).filter(Transmission.transmission_id == transmission_id))
    transmission = result.scalar_one_or_none()
    if not transmission:
        return False

    await db.delete(transmission)
    await db.commit()
    return True
