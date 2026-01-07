from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.car_model import Model
from typing import Optional
from models.brand import Brand


async def create_model(db: AsyncSession, brand_id: int, model_name: str, start_year: Optional[int] = None, end_year: Optional[int] = None):
    """Create a new car model"""
    # Verify brand exists
    brand_result = await db.execute(select(Brand).filter(Brand.brand_id == brand_id))
    if not brand_result.scalar_one_or_none():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Brand with ID {brand_id} does not exist")

    new_model = Model(
        brand_id=brand_id,
        model_name=model_name,
        start_year=start_year,
        end_year=end_year
    )
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    return new_model



async def get_model_by_id(db: AsyncSession, model_id: int):
    """Get a model by ID"""
    result = await db.execute(select(Model).filter(Model.model_id == model_id))
    return result.scalar_one_or_none()


async def get_all_models(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all models with pagination"""
    result = await db.execute(select(Model).offset(skip).limit(limit))
    return result.scalars().all()


async def get_models_by_brand(db: AsyncSession, brand_id: int):
    """Get all models for a specific brand"""
    result = await db.execute(select(Model).filter(Model.brand_id == brand_id))
    return result.scalars().all()


async def update_model(db: AsyncSession, model_id: int, brand_id: Optional[int] = None, model_name: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None):
    """Update a model"""
    result = await db.execute(select(Model).filter(Model.model_id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        return None

    if brand_id is not None:
        model.brand_id = brand_id
    if model_name is not None:
        model.model_name = model_name
    if start_year is not None:
        model.start_year = start_year
    if end_year is not None:
        model.end_year = end_year

    await db.commit()
    await db.refresh(model)
    return model


async def delete_model(db: AsyncSession, model_id: int):
    """Delete a model"""
    result = await db.execute(select(Model).filter(Model.model_id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        return False

    await db.delete(model)
    await db.commit()
    return True
