# File: `routes/lookup_routes.py`
from fastapi import APIRouter, Query, HTTPException
from controllers.lookup_controller import (
    get_all_makes,
    get_models_by_make,
    get_years_by_make_model,
)

router = APIRouter(prefix="/lookup", tags=["Lookup"])


@router.get("/makes")
def makes():
    """
    Return JSON with `items` array so frontend select gets expected shape.
    """
    items = get_all_makes()
    return {"items": items}


@router.get("/models")
def models(make: str = Query(...)):
    if not make:
        raise HTTPException(status_code=400, detail="make is required")
    items = get_models_by_make(make)
    return {"items": items}


@router.get("/years")
def years(make: str = Query(...), model: str = Query(...)):
    if not make or not model:
        raise HTTPException(status_code=400, detail="make and model are required")
    items = get_years_by_make_model(make, model)
    return {"items": items}
