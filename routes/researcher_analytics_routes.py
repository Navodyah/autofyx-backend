from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.postgresql import get_db
from controllers.researcher_analytics_controller import get_researcher_analytics


router = APIRouter(prefix="/researcher", tags=["researcher-analytics"])


@router.get("/analytics")
async def get_researcher_analytics_route(db: AsyncSession = Depends(get_db)):
    return await get_researcher_analytics(db)