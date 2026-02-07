# python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.engine import EngineType
from typing import Optional


async def create_engine_type(db: AsyncSession, engine_type_name: str, cylinders: int):
    new_engine_type = EngineType(
        engine_type_name=engine_type_name,
        cylinders=cylinders
    )
    db.add(new_engine_type)
    await db.commit()
    await db.refresh(new_engine_type)
    return new_engine_type


async def get_engine_type_by_id(db: AsyncSession, engine_type_id: int):
    result = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    return result.scalar_one_or_none()


async def get_all_engine_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(EngineType).offset(skip).limit(limit))
    return result.scalars().all()


async def update_engine_type(db: AsyncSession, engine_type_id: int, engine_type_name: Optional[str] = None, cylinders: Optional[int] = None):
    result = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    engine_type = result.scalar_one_or_none()
    if not engine_type:
        return None

    if engine_type_name is not None:
        engine_type.engine_type_name = engine_type_name
    if cylinders is not None:
        engine_type.cylinders = cylinders

    await db.commit()
    await db.refresh(engine_type)
    return engine_type


async def delete_engine_type(db: AsyncSession, engine_type_id: int):
    result = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    engine_type = result.scalar_one_or_none()
    if not engine_type:
        return False

    await db.delete(engine_type)
    await db.commit()
    return True
