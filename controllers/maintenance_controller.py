from sqlalchemy.orm import Session
from models.maintenance import MaintenanceCost
from typing import Optional
from decimal import Decimal
from datetime import date


def create_maintenance_cost(db: Session, vehicle_id: int, yearly_cost: Decimal, recorded_date: date, source: Optional[str] = None):
    """Create a new maintenance cost record"""
    new_maintenance_cost = MaintenanceCost(
        vehicle_id=vehicle_id,
        yearly_cost=yearly_cost,
        recorded_date=recorded_date,
        source=source
    )
    db.add(new_maintenance_cost)
    db.commit()
    db.refresh(new_maintenance_cost)
    return new_maintenance_cost


def get_maintenance_cost_by_id(db: Session, record_id: int):
    """Get a maintenance cost record by ID"""
    return db.query(MaintenanceCost).filter(MaintenanceCost.record_id == record_id).first()


def get_all_maintenance_costs(db: Session, skip: int = 0, limit: int = 100):
    """Get all maintenance cost records with pagination"""
    return db.query(MaintenanceCost).offset(skip).limit(limit).all()


def get_maintenance_costs_by_vehicle(db: Session, vehicle_id: int):
    """Get all maintenance cost records for a specific vehicle"""
    return db.query(MaintenanceCost).filter(MaintenanceCost.vehicle_id == vehicle_id).all()


def update_maintenance_cost(db: Session, record_id: int, vehicle_id: Optional[int] = None, yearly_cost: Optional[Decimal] = None, recorded_date: Optional[date] = None, source: Optional[str] = None):
    """Update a maintenance cost record"""
    maintenance_cost = db.query(MaintenanceCost).filter(MaintenanceCost.record_id == record_id).first()
    if not maintenance_cost:
        return None

    if vehicle_id is not None:
        maintenance_cost.vehicle_id = vehicle_id
    if yearly_cost is not None:
        maintenance_cost.yearly_cost = yearly_cost
    if recorded_date is not None:
        maintenance_cost.recorded_date = recorded_date
    if source is not None:
        maintenance_cost.source = source

    db.commit()
    db.refresh(maintenance_cost)
    return maintenance_cost


def delete_maintenance_cost(db: Session, record_id: int):
    """Delete a maintenance cost record"""
    maintenance_cost = db.query(MaintenanceCost).filter(MaintenanceCost.record_id == record_id).first()
    if not maintenance_cost:
        return False

    db.delete(maintenance_cost)
    db.commit()
    return True
