from sqlalchemy.orm import Session
from models.oil import OilQuality
from typing import Optional


def create_oil_quality(db: Session, oil_grade: str, description: Optional[str] = None):
    """Create a new oil quality"""
    new_oil_quality = OilQuality(
        oil_grade=oil_grade,
        description=description
    )
    db.add(new_oil_quality)
    db.commit()
    db.refresh(new_oil_quality)
    return new_oil_quality


def get_oil_quality_by_id(db: Session, oil_id: int):
    """Get an oil quality by ID"""
    return db.query(OilQuality).filter(OilQuality.oil_id == oil_id).first()


def get_all_oil_qualities(db: Session, skip: int = 0, limit: int = 100):
    """Get all oil qualities with pagination"""
    return db.query(OilQuality).offset(skip).limit(limit).all()


def update_oil_quality(db: Session, oil_id: int, oil_grade: Optional[str] = None, description: Optional[str] = None):
    """Update an oil quality"""
    oil_quality = db.query(OilQuality).filter(OilQuality.oil_id == oil_id).first()
    if not oil_quality:
        return None

    if oil_grade is not None:
        oil_quality.oil_grade = oil_grade
    if description is not None:
        oil_quality.description = description

    db.commit()
    db.refresh(oil_quality)
    return oil_quality


def delete_oil_quality(db: Session, oil_id: int):
    """Delete an oil quality"""
    oil_quality = db.query(OilQuality).filter(OilQuality.oil_id == oil_id).first()
    if not oil_quality:
        return False

    db.delete(oil_quality)
    db.commit()
    return True
