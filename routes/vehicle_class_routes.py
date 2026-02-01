from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.vehicle_class_controller import (
    create_vehicle_class,
    get_vehicle_class_by_id,
    get_all_vehicle_classes,
    update_vehicle_class,
    delete_vehicle_class
)
from schemas.vehicle_class_schema import VehicleClassCreate, VehicleClassUpdate, VehicleClassResponse
from typing import List

router = APIRouter(prefix="/vehicle_classes", tags=["vehicle-classes"])


@router.post("/", response_model=VehicleClassResponse, status_code=201)
async def create_vehicle_class_route(vehicle_class: VehicleClassCreate, db: AsyncSession = Depends(get_db)):
    """Create a new vehicle class"""
    return await create_vehicle_class(db, vehicle_class.class_name)


@router.get("/{class_id}", response_model=VehicleClassResponse)
async def get_vehicle_class_route(class_id: int, db: AsyncSession = Depends(get_db)):
    """Get a vehicle class by ID"""
    vehicle_class = await get_vehicle_class_by_id(db, class_id)
    if not vehicle_class:
        raise HTTPException(status_code=404, detail="Vehicle class not found")
    return vehicle_class


@router.get("/", response_model=List[VehicleClassResponse])
async def get_all_vehicle_classes_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all vehicle classes"""
    return await get_all_vehicle_classes(db, skip, limit)


@router.put("/{class_id}", response_model=VehicleClassResponse)
async def update_vehicle_class_route(class_id: int, vehicle_class: VehicleClassUpdate, db: AsyncSession = Depends(get_db)):
    """Update a vehicle class"""
    updated_vehicle_class = await update_vehicle_class(db, class_id, vehicle_class.class_name)
    if not updated_vehicle_class:
        raise HTTPException(status_code=404, detail="Vehicle class not found")
    return updated_vehicle_class


@router.delete("/{class_id}", status_code=204)
async def delete_vehicle_class_route(class_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a vehicle class"""
    success = await delete_vehicle_class(db, class_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle class not found")
    return None
