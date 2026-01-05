from sqlalchemy.orm import Session
from models.vehicle_class import VehicleClass
from typing import Optional


def create_vehicle_class(db: Session, class_name: str):
    """Create a new vehicle class"""
    new_vehicle_class = VehicleClass(class_name=class_name)
    db.add(new_vehicle_class)
    db.commit()
    db.refresh(new_vehicle_class)
    return new_vehicle_class


def get_vehicle_class_by_id(db: Session, class_id: int):
    """Get a vehicle class by ID"""
    return db.query(VehicleClass).filter(VehicleClass.class_id == class_id).first()


def get_all_vehicle_classes(db: Session, skip: int = 0, limit: int = 100):
    """Get all vehicle classes with pagination"""
    return db.query(VehicleClass).offset(skip).limit(limit).all()


def update_vehicle_class(db: Session, class_id: int, class_name: str):
    """Update a vehicle class"""
    vehicle_class = db.query(VehicleClass).filter(VehicleClass.class_id == class_id).first()
    if not vehicle_class:
        return None

    vehicle_class.class_name = class_name
    db.commit()
    db.refresh(vehicle_class)
    return vehicle_class


def delete_vehicle_class(db: Session, class_id: int):
    """Delete a vehicle class"""
    vehicle_class = db.query(VehicleClass).filter(VehicleClass.class_id == class_id).first()
    if not vehicle_class:
        return False

    db.delete(vehicle_class)
    db.commit()
    return True
