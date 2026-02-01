from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.maintenance import MaintenanceCost
from typing import Optional
from decimal import Decimal
from datetime import date
from sqlalchemy import delete as sa_delete

async def create_maintenance_cost(db: AsyncSession, vehicle_id: int, yearly_cost: Decimal, recorded_date: date, source: Optional[str] = None):
    """Create a new maintenance cost record"""
    new_maintenance_cost = MaintenanceCost(
        vehicle_id=vehicle_id,
        yearly_cost=yearly_cost,
        recorded_date=recorded_date,
        source=source
    )
    db.add(new_maintenance_cost)
    await db.commit()
    await db.refresh(new_maintenance_cost)
    return new_maintenance_cost


async def get_maintenance_cost_by_id(db: AsyncSession, record_id: int):
    """Get a maintenance cost record by ID"""
    result = await db.execute(select(MaintenanceCost).filter(MaintenanceCost.record_id == record_id))
    return result.scalar_one_or_none()


async def get_all_maintenance_costs(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all maintenance cost records with pagination"""
    result = await db.execute(select(MaintenanceCost).offset(skip).limit(limit))
    return result.scalars().all()


async def get_maintenance_costs_by_vehicle(db: AsyncSession, vehicle_id: int):
    """Get all maintenance cost records for a specific vehicle"""
    result = await db.execute(select(MaintenanceCost).filter(MaintenanceCost.vehicle_id == vehicle_id))
    return result.scalars().all()


async def update_maintenance_cost(db: AsyncSession, record_id: int, vehicle_id: Optional[int] = None, yearly_cost: Optional[Decimal] = None, recorded_date: Optional[date] = None, source: Optional[str] = None):
    """Update a maintenance cost record"""
    result = await db.execute(select(MaintenanceCost).filter(MaintenanceCost.record_id == record_id))
    maintenance_cost = result.scalar_one_or_none()
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

    await db.commit()
    await db.refresh(maintenance_cost)
    return maintenance_cost


async def delete_maintenance_cost(db: AsyncSession, record_id: int) -> bool:
    """
    Delete a maintenance cost record using a SQL DELETE and commit.
    Returns True if a row was deleted, False otherwise.
    """
    stmt = sa_delete(MaintenanceCost).where(MaintenanceCost.record_id == record_id)
    result = await db.execute(stmt)
    await db.commit()
    return (result.rowcount or 0) > 0
