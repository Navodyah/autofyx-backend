from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.model_controller import (
    create_model,
    get_model_by_id,
    get_all_models,
    get_models_by_brand,
    update_model,
    delete_model
)
from schemas.model_schema import ModelCreate, ModelUpdate, ModelResponse
from typing import List
from models.brand import Brand

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/available-brands", response_model=List[dict])
async def get_available_brands_route(db: AsyncSession = Depends(get_db)):
    """Get all available brands for dropdown selection"""
    result = await db.execute(select(Brand.brand_id, Brand.brand_name))
    brands = result.all()
    return [{"brand_id": brand_id, "brand_name": brand_name} for brand_id, brand_name in brands]

@router.post("/", response_model=ModelResponse, status_code=201)
async def create_model_route(model: ModelCreate, db: AsyncSession = Depends(get_db)):
    """Create a new car model"""
    try:
        return await create_model(
            db,
            model.brand_id,
            model.model_name,
            model.start_year,
            model.end_year
        )
    except Exception as e:
        await db.rollback()
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Brand with ID {model.brand_id} does not exist")
        raise HTTPException(status_code=500, detail=str(e))





@router.get("/{model_id}", response_model=ModelResponse)
async def get_model_route(model_id: int, db: AsyncSession = Depends(get_db)):
    """Get a model by ID"""
    model = await get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/", response_model=List[ModelResponse])
async def get_all_models_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all models"""
    return await get_all_models(db, skip, limit)


@router.get("/brand/{brand_id}", response_model=List[ModelResponse])
async def get_models_by_brand_route(brand_id: int, db: AsyncSession = Depends(get_db)):
    """Get all models for a specific brand"""
    return await get_models_by_brand(db, brand_id)


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model_route(model_id: int, model: ModelUpdate, db: AsyncSession = Depends(get_db)):
    """Update a model"""
    updated_model = await update_model(
        db,
        model_id,
        model.brand_id,
        model.model_name,
        model.start_year,
        model.end_year
    )
    if not updated_model:
        raise HTTPException(status_code=404, detail="Model not found")
    return updated_model


@router.delete("/{model_id}", status_code=204)
async def delete_model_route(model_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a model"""
    success = await delete_model(db, model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return None
