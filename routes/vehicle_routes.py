from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.vehicle_controller import (
    create_vehicle,
    get_vehicle_by_id,
    get_all_vehicles,
    get_vehicles_by_model,
    update_vehicle,
    delete_vehicle
)
from schemas.vehicle_schema import VehicleCreate, VehicleUpdate, VehicleResponse
from typing import List

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/", response_model=VehicleResponse, status_code=201)
async def create_vehicle_route(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new vehicle"""
    return await create_vehicle(
        db,
        vehicle.model_id,
        vehicle.class_id,
        vehicle.engine_type_id,
        vehicle.fuel_type_id,
        vehicle.transmission_id,
        vehicle.oil_id,
        vehicle.tyre_size,
        vehicle.fuel_efficiency_highway,
        vehicle.fuel_efficiency_combined,
        vehicle.description
    )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle_route(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Get a vehicle by ID"""
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.get("/", response_model=List[VehicleResponse])
async def get_all_vehicles_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all vehicles"""
    return await get_all_vehicles(db, skip, limit)


@router.get("/model/{model_id}", response_model=List[VehicleResponse])
async def get_vehicles_by_model_route(model_id: int, db: AsyncSession = Depends(get_db)):
    """Get all vehicles for a specific model"""
    return await get_vehicles_by_model(db, model_id)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle_route(vehicle_id: int, vehicle: VehicleUpdate, db: AsyncSession = Depends(get_db)):
    """Update a vehicle"""
    updated_vehicle = await update_vehicle(
        db,
        vehicle_id,
        vehicle.model_id,
        vehicle.class_id,
        vehicle.engine_type_id,
        vehicle.fuel_type_id,
        vehicle.transmission_id,
        vehicle.oil_id,
        vehicle.tyre_size,
        vehicle.fuel_efficiency_highway,
        vehicle.fuel_efficiency_combined,
        vehicle.description
    )
    if not updated_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return updated_vehicle


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle_route(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a vehicle"""
    success = await delete_vehicle(db, vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None
