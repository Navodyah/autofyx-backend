from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.fuel import FuelType
from typing import Optional


async def create_fuel_type(db: AsyncSession, fuel_type_id: int, fuel_type_name: str):
    """Create a new fuel type"""
    new_fuel_type = FuelType(fuel_type_id=fuel_type_id, fuel_type_name=fuel_type_name)
    db.add(new_fuel_type)
    await db.commit()
    await db.refresh(new_fuel_type)
    return new_fuel_type


async def get_fuel_type_by_id(db: AsyncSession, fuel_type_id: int):
    """Get a fuel type by ID"""
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    return result.scalar_one_or_none()


async def get_all_fuel_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all fuel types with pagination"""
    result = await db.execute(select(FuelType).offset(skip).limit(limit))
    return result.scalars().all()


async def update_fuel_type(db: AsyncSession, fuel_type_id: int, fuel_type_name: str):
    """Update a fuel type"""
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return None

    fuel_type.fuel_type_name = fuel_type_name
    await db.commit()
    await db.refresh(fuel_type)
    return fuel_type


async def delete_fuel_type(db: AsyncSession, fuel_type_id: int):
    """Delete a fuel type"""
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return False

    await db.delete(fuel_type)
    await db.commit()
    return True
