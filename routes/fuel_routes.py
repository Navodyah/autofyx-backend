from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.fuel_controller import (
    create_fuel_type,
    get_fuel_type_by_id,
    get_all_fuel_types,
    update_fuel_type,
    delete_fuel_type,
    scrape_fuel_prices,
    bulk_update_fuel_prices
)
from schemas.fuel_schema import FuelTypeCreate, FuelTypeUpdate, FuelTypeResponse
from typing import List, Dict, Any

router = APIRouter(prefix="/fuel_types", tags=["fuel-types"])


@router.get("/scrape")
async def scrape_fuel_prices_route():
    """Scrape Ceypetco for fuel prices without saving to DB"""
    result = await scrape_fuel_prices()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/bulk-update")
async def bulk_update_route(updates: Dict[str, float], db: AsyncSession = Depends(get_db)):
    """Bulk update fuel prices given a dict of {fuel_type_id: new_price}"""
    result = await bulk_update_fuel_prices(db, updates)
    return result


@router.post("/", response_model=FuelTypeResponse, status_code=201)
async def create_fuel_type_route(fuel_type: FuelTypeCreate, db: AsyncSession = Depends(get_db)):
    """Create a new fuel type"""
    return await create_fuel_type(db, fuel_type.fuel_type_name, fuel_type.fuel_price)


@router.get("/{fuel_type_id}", response_model=FuelTypeResponse)
async def get_fuel_type_route(fuel_type_id: int, db: AsyncSession = Depends(get_db)):
    fuel_type = await get_fuel_type_by_id(db, fuel_type_id)
    if not fuel_type:
        raise HTTPException(status_code=404, detail="Fuel type not found")
    return fuel_type


@router.get("/", response_model=List[FuelTypeResponse])
async def get_all_fuel_types_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await get_all_fuel_types(db, skip, limit)


@router.put("/{fuel_type_id}", response_model=FuelTypeResponse)
async def update_fuel_type_route(fuel_type_id: int, fuel_type: FuelTypeUpdate, db: AsyncSession = Depends(get_db)):
    updated_fuel_type = await update_fuel_type(
        db,
        fuel_type_id,
        fuel_type.fuel_type_name,
        fuel_type.fuel_price,
    )
    if not updated_fuel_type:
        raise HTTPException(status_code=404, detail="Fuel type not found")
    return updated_fuel_type


@router.delete("/{fuel_type_id}", status_code=204)
async def delete_fuel_type_route(fuel_type_id: int, db: AsyncSession = Depends(get_db)):
    success = await delete_fuel_type(db, fuel_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fuel type not found")
    return None
