from sqlalchemy.orm import Session
from models.transmission import Transmission
from typing import Optional


def create_transmission(db: Session, transmission_name: str, category: Optional[str] = None):
    """Create a new transmission"""
    new_transmission = Transmission(
        transmission_name=transmission_name,
        category=category
    )
    db.add(new_transmission)
    db.commit()
    db.refresh(new_transmission)
    return new_transmission


def get_transmission_by_id(db: Session, transmission_id: int):
    """Get a transmission by ID"""
    return db.query(Transmission).filter(Transmission.transmission_id == transmission_id).first()


def get_all_transmissions(db: Session, skip: int = 0, limit: int = 100):
    """Get all transmissions with pagination"""
    return db.query(Transmission).offset(skip).limit(limit).all()


def update_transmission(db: Session, transmission_id: int, transmission_name: Optional[str] = None, category: Optional[str] = None):
    """Update a transmission"""
    transmission = db.query(Transmission).filter(Transmission.transmission_id == transmission_id).first()
    if not transmission:
        return None

    if transmission_name is not None:
        transmission.transmission_name = transmission_name
    if category is not None:
        transmission.category = category

    db.commit()
    db.refresh(transmission)
    return transmission


def delete_transmission(db: Session, transmission_id: int):
    """Delete a transmission"""
    transmission = db.query(Transmission).filter(Transmission.transmission_id == transmission_id).first()
    if not transmission:
        return False

    db.delete(transmission)
    db.commit()
    return True
