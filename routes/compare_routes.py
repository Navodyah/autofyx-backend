# python
# File: `routes/compare_routes.py`
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from config.postgresql import get_db
from controllers.compare_controller import compare_vehicles as compare_vehicles_controller

router = APIRouter(prefix="/compare", tags=["Compare"])


class Selection(BaseModel):
    make: str
    model: str
    year: int


@router.post("/", response_model=List[Dict[str, Any]])
async def compare_endpoint(
    payload: Any = Body(...),
    session: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Accept either:
      - a JSON array: [{make:, model:, year:}, ...]
      - or a wrapper object: { "selections": [ ... ] }
    Normalizes and validates into a list of selections, then calls the controller.
    """
    # Normalize payload to a list of raw selection dicts
    if isinstance(payload, dict) and "selections" in payload:
        raw_selections = payload["selections"]
    elif isinstance(payload, list):
        raw_selections = payload
    else:
        raise HTTPException(status_code=422, detail="Body must be a list or an object with 'selections' list")

    if not isinstance(raw_selections, list) or not raw_selections:
        raise HTTPException(status_code=400, detail="selections is required and must be a non-empty list")

    # Validate each item with Pydantic
    try:
        selections = [sel.dict() for sel in [Selection.parse_obj(item) for item in raw_selections]]
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())

    return await compare_vehicles_controller(session, selections)
