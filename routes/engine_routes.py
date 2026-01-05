from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.engine_controller import (
    create_engine_type,
    get_engine_type_by_id,
    get_all_engine_types,
    update_engine_type,
    delete_engine_type
)
from schemas.engine_schema import EngineTypeCreate, EngineTypeUpdate, EngineTypeResponse
from typing import List

router = APIRouter(prefix="/engine-types", tags=["engine-types"])


@router.post("/", response_model=EngineTypeResponse, status_code=201)
async def create_engine_type_route(engine_type: EngineTypeCreate, db: AsyncSession = Depends(get_db)):
    """Create a new engine type"""
    return await create_engine_type(
        db,
        engine_type.engine_type_id,
        engine_type.engine_type_name,
        engine_type.cylinders,
        engine_type.engine_size
    )


@router.get("/{engine_type_id}", response_model=EngineTypeResponse)
async def get_engine_type_route(engine_type_id: int, db: AsyncSession = Depends(get_db)):
    """Get an engine type by ID"""
    engine_type = await get_engine_type_by_id(db, engine_type_id)
    if not engine_type:
        raise HTTPException(status_code=404, detail="Engine type not found")
    return engine_type


@router.get("/", response_model=List[EngineTypeResponse])
async def get_all_engine_types_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all engine types"""
    return await get_all_engine_types(db, skip, limit)


@router.put("/{engine_type_id}", response_model=EngineTypeResponse)
async def update_engine_type_route(engine_type_id: int, engine_type: EngineTypeUpdate, db: AsyncSession = Depends(get_db)):
    """Update an engine type"""
    updated_engine_type = await update_engine_type(
        db,
        engine_type_id,
        engine_type.engine_type_name,
        engine_type.cylinders,
        engine_type.engine_size
    )
    if not updated_engine_type:
        raise HTTPException(status_code=404, detail="Engine type not found")
    return updated_engine_type


@router.delete("/{engine_type_id}", status_code=204)
async def delete_engine_type_route(engine_type_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an engine type"""
    success = await delete_engine_type(db, engine_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Engine type not found")
    return None
