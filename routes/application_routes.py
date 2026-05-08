from fastapi import APIRouter, status, Body, HTTPException
from controllers.application_controller import apply_for_researcher, list_pending_applications, review_application
from models.application_models import ResearcherApplicationCreate, ResearcherApplicationUpdateStatus

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def create_researcher_application(application: ResearcherApplicationCreate = Body(...)):
    try:
        result = apply_for_researcher(application)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending", status_code=status.HTTP_200_OK)
async def get_pending_applications():
    try:
        return {"success": True, "applications": list_pending_applications()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{app_id}/review", status_code=status.HTTP_200_OK)
async def update_application_status(app_id: str, status_data: ResearcherApplicationUpdateStatus = Body(...)):
    if status_data.status not in ["approved", "declined"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'declined'")
        
    try:
        result = review_application(app_id, status_data)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
