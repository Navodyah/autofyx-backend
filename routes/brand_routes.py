from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from config.postgresql import get_db
from controllers.brand_controller import (
    create_brand,
    get_brand_by_id,
    get_all_brands,
    update_brand,
    delete_brand
)
from schemas.brand_schema import BrandCreate, BrandUpdate, BrandResponse
from typing import List

router = APIRouter(prefix="/brands", tags=["brands"])



@router.post("/", response_model=BrandResponse, status_code=201)
async def create_brand_route(brand: BrandCreate, db: AsyncSession = Depends(get_db)):
    """Create a new brand"""
    return await create_brand(db, brand.brand_name, brand.country)



@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand_route(brand_id: int, db: AsyncSession = Depends(get_db)):
    """Get a brand by ID"""
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.get("/", response_model=List[BrandResponse])
async def get_all_brands_route(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all brands"""
    return await get_all_brands(db, skip, limit)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand_route(brand_id: int, brand: BrandUpdate, db: AsyncSession = Depends(get_db)):
    """Update a brand"""
    updated_brand = await update_brand(db, brand_id, brand.brand_name, brand.country)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated_brand


@router.delete("/{brand_id}", status_code=204)
async def delete_brand_route(brand_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a brand"""
    success = await delete_brand(db, brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")
    return None



