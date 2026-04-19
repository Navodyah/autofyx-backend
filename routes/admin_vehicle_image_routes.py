from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from config.postgresql import get_db
from models.vehicle import Vehicle
from services.r2_storage import r2_storage


router = APIRouter(prefix="/admin/vehicle-images", tags=["admin-vehicle-images"])


@router.post("/{vehicle_id}/upload")
async def upload_vehicle_image(vehicle_id: int, image: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    new_key = r2_storage.build_vehicle_key(vehicle_id, image.filename or "image")
    new_url = await run_in_threadpool(
        r2_storage.upload_bytes,
        key=new_key,
        body=image_bytes,
        content_type=image.content_type,
    )

    old_key = r2_storage.extract_key_from_url(vehicle.image_url)
    vehicle.image_url = new_url
    await db.commit()
    await db.refresh(vehicle)

    if old_key and old_key != new_key:
        try:
            await run_in_threadpool(r2_storage.delete_key, old_key)
        except Exception:
            pass

    return {
        "message": "Image uploaded successfully",
        "vehicle_id": vehicle.vehicle_id,
        "image_url": vehicle.image_url,
        "storage_key": new_key,
    }


@router.put("/{vehicle_id}/upload")
async def replace_vehicle_image(vehicle_id: int, image: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await upload_vehicle_image(vehicle_id, image, db)


@router.delete("/{vehicle_id}")
async def delete_vehicle_image(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    old_key = r2_storage.extract_key_from_url(vehicle.image_url)
    vehicle.image_url = None
    await db.commit()

    if old_key:
        try:
            await run_in_threadpool(r2_storage.delete_key, old_key)
        except Exception:
            pass

    return {"message": "Image deleted successfully", "vehicle_id": vehicle_id}