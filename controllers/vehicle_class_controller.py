from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.vehicle_class import VehicleClass


async def create_vehicle_class(db: AsyncSession, class_name: str):
    """Create a new vehicle class"""
    new_vehicle_class = VehicleClass(class_name=class_name)
    db.add(new_vehicle_class)
    await db.commit()
    await db.refresh(new_vehicle_class)
    return new_vehicle_class


async def get_vehicle_class_by_id(db: AsyncSession, class_id: int):
    """Get a vehicle class by ID"""
    result = await db.execute(select(VehicleClass).filter(VehicleClass.class_id == class_id))
    return result.scalar_one_or_none()


async def get_all_vehicle_classes(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all vehicle classes with pagination"""
    result = await db.execute(select(VehicleClass).offset(skip).limit(limit))
    return result.scalars().all()


async def update_vehicle_class(db: AsyncSession, class_id: int, class_name: str):
    """Update a vehicle class"""
    result = await db.execute(select(VehicleClass).filter(VehicleClass.class_id == class_id))
    vehicle_class = result.scalar_one_or_none()
    if not vehicle_class:
        return None

    vehicle_class.class_name = class_name
    await db.commit()
    await db.refresh(vehicle_class)
    return vehicle_class


async def delete_vehicle_class(db: AsyncSession, class_id: int):
    """Delete a vehicle class"""
    result = await db.execute(select(VehicleClass).filter(VehicleClass.class_id == class_id))
    vehicle_class = result.scalar_one_or_none()
    if not vehicle_class:
        return False

    await db.delete(vehicle_class)
    await db.commit()
    return True
