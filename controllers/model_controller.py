from sqlalchemy.orm import Session
from models.car_model import Model
from typing import Optional


def create_model(db: Session, brand_id: int, model_name: str, start_year: Optional[int] = None, end_year: Optional[int] = None):
    """Create a new car model"""
    new_model = Model(
        brand_id=brand_id,
        model_name=model_name,
        start_year=start_year,
        end_year=end_year
    )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return new_model


def get_model_by_id(db: Session, model_id: int):
    """Get a model by ID"""
    return db.query(Model).filter(Model.model_id == model_id).first()


def get_all_models(db: Session, skip: int = 0, limit: int = 100):
    """Get all models with pagination"""
    return db.query(Model).offset(skip).limit(limit).all()


def get_models_by_brand(db: Session, brand_id: int):
    """Get all models for a specific brand"""
    return db.query(Model).filter(Model.brand_id == brand_id).all()


def update_model(db: Session, model_id: int, brand_id: Optional[int] = None, model_name: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None):
    """Update a model"""
    model = db.query(Model).filter(Model.model_id == model_id).first()
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

    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: int):
    """Delete a model"""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        return False

    db.delete(model)
    db.commit()
    return True
