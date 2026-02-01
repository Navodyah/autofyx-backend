from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.maintenance_controller import (
    create_maintenance_cost,
    get_maintenance_cost_by_id,
    get_all_maintenance_costs,
    get_maintenance_costs_by_vehicle,
    update_maintenance_cost,
    delete_maintenance_cost
)
from schemas.maintenance_schema import MaintenanceCostCreate, MaintenanceCostUpdate, MaintenanceCostResponse
from typing import List

router = APIRouter(prefix="/maintenance-costs", tags=["maintenance-costs"])


@router.post("/", response_model=MaintenanceCostResponse, status_code=201)
async def create_maintenance_cost_route(maintenance_cost: MaintenanceCostCreate, db: AsyncSession = Depends(get_db)):
    """Create a new maintenance cost record"""
    return await create_maintenance_cost(
        db,
        maintenance_cost.vehicle_id,
        maintenance_cost.yearly_cost,
        maintenance_cost.recorded_date,
        maintenance_cost.source
    )


@router.get("/{record_id}", response_model=MaintenanceCostResponse)
async def get_maintenance_cost_route(record_id: int, db: AsyncSession = Depends(get_db)):
    """Get a maintenance cost record by ID"""
    maintenance_cost = await get_maintenance_cost_by_id(db, record_id)
    if not maintenance_cost:
        raise HTTPException(status_code=404, detail="Maintenance cost record not found")
    return maintenance_cost


@router.get("/", response_model=List[MaintenanceCostResponse])
async def get_all_maintenance_costs_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all maintenance cost records"""
    return await get_all_maintenance_costs(db, skip, limit)


@router.get("/vehicle/{vehicle_id}", response_model=List[MaintenanceCostResponse])
async def get_maintenance_costs_by_vehicle_route(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Get all maintenance cost records for a specific vehicle"""
    return await get_maintenance_costs_by_vehicle(db, vehicle_id)


@router.put("/{record_id}", response_model=MaintenanceCostResponse)
async def update_maintenance_cost_route(record_id: int, maintenance_cost: MaintenanceCostUpdate, db: AsyncSession = Depends(get_db)):
    """Update a maintenance cost record"""
    updated_maintenance_cost = await update_maintenance_cost(
        db,
        record_id,
        maintenance_cost.vehicle_id,
        maintenance_cost.yearly_cost,
        maintenance_cost.recorded_date,
        maintenance_cost.source
    )
    if not updated_maintenance_cost:
        raise HTTPException(status_code=404, detail="Maintenance cost record not found")
    return updated_maintenance_cost


@router.delete("/{record_id}")
async def delete_maintenance_cost_route(record_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a maintenance cost record and return JSON so clients can refresh view reliably."""
    success = await delete_maintenance_cost(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Maintenance cost record not found")
    return {"deleted": record_id}