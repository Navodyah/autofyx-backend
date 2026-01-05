from sqlalchemy.orm import Session
from models.vehicle import Vehicle
from typing import Optional
from decimal import Decimal


def create_vehicle(
    db: Session,
    model_id: int,
    class_id: int,
    engine_type_id: int,
    fuel_type_id: int,
    transmission_id: int,
    oil_id: int,
    tyre_size: Optional[str] = None,
    fuel_efficiency_highway: Optional[Decimal] = None,
    fuel_efficiency_combined: Optional[Decimal] = None,
    description: Optional[str] = None
):
    """Create a new vehicle"""
    new_vehicle = Vehicle(
        model_id=model_id,
        class_id=class_id,
        engine_type_id=engine_type_id,
        fuel_type_id=fuel_type_id,
        transmission_id=transmission_id,
        oil_id=oil_id,
        tyre_size=tyre_size,
        fuel_efficiency_highway=fuel_efficiency_highway,
        fuel_efficiency_combined=fuel_efficiency_combined,
        description=description
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


def get_vehicle_by_id(db: Session, vehicle_id: int):
    """Get a vehicle by ID"""
    return db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()


def get_all_vehicles(db: Session, skip: int = 0, limit: int = 100):
    """Get all vehicles with pagination"""
    return db.query(Vehicle).offset(skip).limit(limit).all()


def get_vehicles_by_model(db: Session, model_id: int):
    """Get all vehicles for a specific model"""
    return db.query(Vehicle).filter(Vehicle.model_id == model_id).all()


def update_vehicle(
    db: Session,
    vehicle_id: int,
    model_id: Optional[int] = None,
    class_id: Optional[int] = None,
    engine_type_id: Optional[int] = None,
    fuel_type_id: Optional[int] = None,
    transmission_id: Optional[int] = None,
    oil_id: Optional[int] = None,
    tyre_size: Optional[str] = None,
    fuel_efficiency_highway: Optional[Decimal] = None,
    fuel_efficiency_combined: Optional[Decimal] = None,
    description: Optional[str] = None
):
    """Update a vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        return None

    if model_id is not None:
        vehicle.model_id = model_id
    if class_id is not None:
        vehicle.class_id = class_id
    if engine_type_id is not None:
        vehicle.engine_type_id = engine_type_id
    if fuel_type_id is not None:
        vehicle.fuel_type_id = fuel_type_id
    if transmission_id is not None:
        vehicle.transmission_id = transmission_id
    if oil_id is not None:
        vehicle.oil_id = oil_id
    if tyre_size is not None:
        vehicle.tyre_size = tyre_size
    if fuel_efficiency_highway is not None:
        vehicle.fuel_efficiency_highway = fuel_efficiency_highway
    if fuel_efficiency_combined is not None:
        vehicle.fuel_efficiency_combined = fuel_efficiency_combined
    if description is not None:
        vehicle.description = description

    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, vehicle_id: int):
    """Delete a vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        return False

    db.delete(vehicle)
    db.commit()
    return True
