from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.engine import EngineType
from typing import Optional
from decimal import Decimal


async def create_engine_type(db: AsyncSession, engine_type_id: int, engine_type_name: str, cylinders: int, engine_size: Decimal):
    """Create a new engine type"""
    new_engine_type = EngineType(
        engine_type_id=engine_type_id,
        engine_type_name=engine_type_name,
        cylinders=cylinders,
        engine_size=engine_size
    )
    db.add(new_engine_type)
    await db.commit()
    await db.refresh(new_engine_type)
    return new_engine_type


async def get_engine_type_by_id(db: AsyncSession, engine_type_id: int):
    """Get an engine type by ID"""
    result = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    return result.scalar_one_or_none()


async def get_all_engine_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all engine types with pagination"""
    result = await db.execute(select(EngineType).offset(skip).limit(limit))
    return result.scalars().all()


async def update_engine_type(db: AsyncSession, engine_type_id: int, engine_type_name: Optional[str] = None, cylinders: Optional[int] = None, engine_size: Optional[Decimal] = None):
    """Update an engine type"""
    result = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    engine_type = result.scalar_one_or_none()
    if not engine_type:
        return None

    if engine_type_name is not None:
        engine_type.engine_type_name = engine_type_name
    if cylinders is not None:
        engine_type.cylinders = cylinders
    if engine_size is not None:
        engine_type.engine_size = engine_size

    await db.commit()
    await db.refresh(engine_type)
    return engine_type


async def delete_engine_type(db: AsyncSession, engine_type_id: int):
    """Delete an engine type"""
    result = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    engine_type = result.scalar_one_or_none()
    if not engine_type:
        return False

    await db.delete(engine_type)
    await db.commit()
    return True
