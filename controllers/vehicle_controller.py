# python
# File: `controllers/vehicle_controller.py`
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from sqlalchemy import delete as sa_delete

from models.vehicle import Vehicle
from models.car_model import Model
from models.vehicle_class import VehicleClass
from models.engine import EngineType
from models.fuel import FuelType
from models.transmission import Transmission
from models.oil import OilQuality


async def get_all_vehicles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Vehicle]:
    stmt = (
        select(Vehicle)
        .options(
            selectinload(Vehicle.model),
            selectinload(Vehicle.vehicle_class),
            selectinload(Vehicle.engine_type),
            selectinload(Vehicle.fuel_type),
            selectinload(Vehicle.transmission),
            selectinload(Vehicle.oil_quality),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_vehicles_by_model(db: AsyncSession, model_id: int) -> List[Vehicle]:
    """
    Return list of Vehicle instances for a given model_id with relationships loaded.
    """
    stmt = (
        select(Vehicle)
        .options(
            selectinload(Vehicle.model),
            selectinload(Vehicle.vehicle_class),
            selectinload(Vehicle.engine_type),
            selectinload(Vehicle.fuel_type),
            selectinload(Vehicle.transmission),
            selectinload(Vehicle.oil_quality),
        )
        .filter(Vehicle.model_id == model_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_vehicle(
    db: AsyncSession,
    model_id: int,
    class_id: int,
    engine_type_id: int,
    fuel_type_id: int,
    transmission_id: int,
    oil_id: int,
    manufacturing_year: int,
    tyre_size: Optional[str] = None,
    fuel_efficiency_highway: Optional[Decimal] = None,
    fuel_efficiency_combined: Optional[Decimal] = None,
    description: Optional[str] = None
):
    # Validate foreign keys
    model = await db.execute(select(Model).filter(Model.model_id == model_id))
    if not model.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Model with ID {model_id} does not exist")

    vehicle_class = await db.execute(select(VehicleClass).filter(VehicleClass.class_id == class_id))
    if not vehicle_class.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Vehicle class with ID {class_id} does not exist")

    engine_type = await db.execute(select(EngineType).filter(EngineType.engine_type_id == engine_type_id))
    if not engine_type.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Engine type with ID {engine_type_id} does not exist")

    fuel_type = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    if not fuel_type.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Fuel type with ID {fuel_type_id} does not exist")

    transmission = await db.execute(select(Transmission).filter(Transmission.transmission_id == transmission_id))
    if not transmission.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Transmission with ID {transmission_id} does not exist")

    oil_quality = await db.execute(select(OilQuality).filter(OilQuality.oil_id == oil_id))
    if not oil_quality.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Oil quality with ID {oil_id} does not exist")

    new_vehicle = Vehicle(
        model_id=model_id,
        class_id=class_id,
        engine_type_id=engine_type_id,
        fuel_type_id=fuel_type_id,
        transmission_id=transmission_id,
        oil_id=oil_id,
        manufacturing_year=manufacturing_year,
        tyre_size=tyre_size,
        fuel_efficiency_highway=fuel_efficiency_highway,
        fuel_efficiency_combined=fuel_efficiency_combined,
        description=description
    )
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)
    return new_vehicle


async def get_vehicle_by_id(db: AsyncSession, vehicle_id: int) -> Optional[Vehicle]:
    result = await db.execute(
        select(Vehicle).options(
            selectinload(Vehicle.model),
            selectinload(Vehicle.vehicle_class),
            selectinload(Vehicle.engine_type),
            selectinload(Vehicle.fuel_type),
            selectinload(Vehicle.transmission),
            selectinload(Vehicle.oil_quality),
        ).filter(Vehicle.vehicle_id == vehicle_id)
    )
    return result.scalar_one_or_none()


async def update_vehicle(
    db: AsyncSession,
    vehicle_id: int,
    model_id: Optional[int] = None,
    class_id: Optional[int] = None,
    engine_type_id: Optional[int] = None,
    fuel_type_id: Optional[int] = None,
    transmission_id: Optional[int] = None,
    oil_id: Optional[int] = None,
    manufacturing_year: Optional[int] = None,
    tyre_size: Optional[str] = None,
    fuel_efficiency_highway: Optional[Decimal] = None,
    fuel_efficiency_combined: Optional[Decimal] = None,
    description: Optional[str] = None
):
    result = await db.execute(select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
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
    if manufacturing_year is not None:
        vehicle.manufacturing_year = manufacturing_year
    if tyre_size is not None:
        vehicle.tyre_size = tyre_size
    if fuel_efficiency_highway is not None:
        vehicle.fuel_efficiency_highway = fuel_efficiency_highway
    if fuel_efficiency_combined is not None:
        vehicle.fuel_efficiency_combined = fuel_efficiency_combined
    if description is not None:
        vehicle.description = description

    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def delete_vehicle(db: AsyncSession, vehicle_id: int) -> bool:
    """
    Delete a vehicle using a SQL DELETE statement and commit.
    Returns True if a row was deleted, False otherwise.
    """
    stmt = sa_delete(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
    result = await db.execute(stmt)
    await db.commit()
    # rowcount indicates how many rows were affected
    return (result.rowcount or 0) > 0
