from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.fuel import FuelType
from models.vehicle import Vehicle


async def create_fuel_type(db: AsyncSession, fuel_type_name: str, fuel_price: Optional[float] = None):
    """Create a new fuel type (DB generates the ID)."""
    new_fuel_type = FuelType(fuel_type_name=fuel_type_name, fuel_price=fuel_price)
    db.add(new_fuel_type)
    await db.commit()
    await db.refresh(new_fuel_type)
    return await get_fuel_type_by_id(db, new_fuel_type.fuel_type_id)


async def get_fuel_type_by_id(db: AsyncSession, fuel_type_id: int):
    result = await db.execute(
        select(
            FuelType.fuel_type_id,
            FuelType.fuel_type_name,
            FuelType.fuel_price,
            func.avg(Vehicle.fuel_efficiency_combined).label("fuel_efficiency_combined"),
        )
        .outerjoin(Vehicle, Vehicle.fuel_type_id == FuelType.fuel_type_id)
        .where(FuelType.fuel_type_id == fuel_type_id)
        .group_by(FuelType.fuel_type_id, FuelType.fuel_type_name, FuelType.fuel_price)
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_all_fuel_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(
            FuelType.fuel_type_id,
            FuelType.fuel_type_name,
            FuelType.fuel_price,
            func.avg(Vehicle.fuel_efficiency_combined).label("fuel_efficiency_combined"),
        )
        .outerjoin(Vehicle, Vehicle.fuel_type_id == FuelType.fuel_type_id)
        .group_by(FuelType.fuel_type_id, FuelType.fuel_type_name, FuelType.fuel_price)
        .offset(skip)
        .limit(limit)
    )
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def update_fuel_type(
    db: AsyncSession,
    fuel_type_id: int,
    fuel_type_name: str,
    fuel_price: Optional[float] = None,
):
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return None

    fuel_type.fuel_type_name = fuel_type_name
    fuel_type.fuel_price = fuel_price
    await db.commit()
    return await get_fuel_type_by_id(db, fuel_type_id)


async def delete_fuel_type(db: AsyncSession, fuel_type_id: int):
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return False

    await db.delete(fuel_type)
    await db.commit()
    return True
