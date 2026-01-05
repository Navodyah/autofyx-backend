from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from controllers.oil_controller import (
    create_oil_quality,
    get_oil_quality_by_id,
    get_all_oil_qualities,
    update_oil_quality,
    delete_oil_quality
)
from schemas.oil_schema import OilQualityCreate, OilQualityUpdate, OilQualityResponse
from typing import List

router = APIRouter(prefix="/oil-qualities", tags=["oil-qualities"])


@router.post("/", response_model=OilQualityResponse, status_code=201)
async def create_oil_quality_route(oil_quality: OilQualityCreate, db: AsyncSession = Depends(get_db)):
    """Create a new oil quality"""
    return await create_oil_quality(
        db,
        oil_quality.oil_grade,
        oil_quality.description
    )


@router.get("/{oil_id}", response_model=OilQualityResponse)
async def get_oil_quality_route(oil_id: int, db: AsyncSession = Depends(get_db)):
    """Get an oil quality by ID"""
    oil_quality = await get_oil_quality_by_id(db, oil_id)
    if not oil_quality:
        raise HTTPException(status_code=404, detail="Oil quality not found")
    return oil_quality


@router.get("/", response_model=List[OilQualityResponse])
async def get_all_oil_qualities_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all oil qualities"""
    return await get_all_oil_qualities(db, skip, limit)


@router.put("/{oil_id}", response_model=OilQualityResponse)
async def update_oil_quality_route(oil_id: int, oil_quality: OilQualityUpdate, db: AsyncSession = Depends(get_db)):
    """Update an oil quality"""
    updated_oil_quality = await update_oil_quality(
        db,
        oil_id,
        oil_quality.oil_grade,
        oil_quality.description
    )
    if not updated_oil_quality:
        raise HTTPException(status_code=404, detail="Oil quality not found")
    return updated_oil_quality


@router.delete("/{oil_id}", status_code=204)
async def delete_oil_quality_route(oil_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an oil quality"""
    success = await delete_oil_quality(db, oil_id)
    if not success:
        raise HTTPException(status_code=404, detail="Oil quality not found")
    return None
