from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.postgresql import get_db
from controllers.transmission_controller import (
    create_transmission,
    get_transmission_by_id,
    get_all_transmissions,
    update_transmission,
    delete_transmission
)
from schemas.transmission_schema import TransmissionCreate, TransmissionUpdate, TransmissionResponse
from typing import List

router = APIRouter(prefix="/transmissions", tags=["transmissions"])


@router.post("/", response_model=TransmissionResponse, status_code=201)
def create_transmission_route(transmission: TransmissionCreate, db: Session = Depends(get_db)):
    """Create a new transmission"""
    return create_transmission(
        db,
        transmission.transmission_name,
        transmission.category
    )


@router.get("/{transmission_id}", response_model=TransmissionResponse)
def get_transmission_route(transmission_id: int, db: Session = Depends(get_db)):
    """Get a transmission by ID"""
    transmission = get_transmission_by_id(db, transmission_id)
    if not transmission:
        raise HTTPException(status_code=404, detail="Transmission not found")
    return transmission


@router.get("/", response_model=List[TransmissionResponse])
def get_all_transmissions_route(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all transmissions"""
    return get_all_transmissions(db, skip, limit)


@router.put("/{transmission_id}", response_model=TransmissionResponse)
def update_transmission_route(transmission_id: int, transmission: TransmissionUpdate, db: Session = Depends(get_db)):
    """Update a transmission"""
    updated_transmission = update_transmission(
        db,
        transmission_id,
        transmission.transmission_name,
        transmission.category
    )
    if not updated_transmission:
        raise HTTPException(status_code=404, detail="Transmission not found")
    return updated_transmission


@router.delete("/{transmission_id}", status_code=204)
def delete_transmission_route(transmission_id: int, db: Session = Depends(get_db)):
    """Delete a transmission"""
    success = delete_transmission(db, transmission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transmission not found")
    return None
