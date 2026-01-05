from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/", response_model=ModelResponse, status_code=201)
def create_model_route(model: ModelCreate, db: Session = Depends(get_db)):
    """Create a new car model"""
    return create_model(
        db,
        model.brand_id,
        model.model_name,
        model.start_year,
        model.end_year
    )


@router.get("/{model_id}", response_model=ModelResponse)
def get_model_route(model_id: int, db: Session = Depends(get_db)):
    """Get a model by ID"""
    model = get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/", response_model=List[ModelResponse])
def get_all_models_route(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all models"""
    return get_all_models(db, skip, limit)


@router.get("/brand/{brand_id}", response_model=List[ModelResponse])
def get_models_by_brand_route(brand_id: int, db: Session = Depends(get_db)):
    """Get all models for a specific brand"""
    return get_models_by_brand(db, brand_id)


@router.put("/{model_id}", response_model=ModelResponse)
def update_model_route(model_id: int, model: ModelUpdate, db: Session = Depends(get_db)):
    """Update a model"""
    updated_model = update_model(
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
def delete_model_route(model_id: int, db: Session = Depends(get_db)):
    """Delete a model"""
    success = delete_model(db, model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return None
