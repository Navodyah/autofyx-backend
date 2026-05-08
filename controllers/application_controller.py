from services.application_service import create_application, get_pending_applications, update_application_status
from models.application_models import ResearcherApplicationCreate, ResearcherApplicationUpdateStatus

def apply_for_researcher(application_data: ResearcherApplicationCreate):
    return create_application(application_data.model_dump())

def list_pending_applications():
    return get_pending_applications()

def review_application(app_id: str, status_data: ResearcherApplicationUpdateStatus):
    return update_application_status(app_id, status_data.status)
