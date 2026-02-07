from __future__ import annotations

from fastapi import APIRouter

from controllers.recommender_controller import RecommendationController
from schemas.recommender_schemas import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

controller = RecommendationController()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """
    POST /recommendations
    Body example:
    {
      "monthly_income": 1000000,
      "purpose": "luxury",
      "area": "Highway",
      "fuel": "Z - Premium Gasoline",
      "transmission": "A=Automatic",
      "max_comb_l_per_100": 15,
      "top_n": 10,
      "candidate_limit": 2000
    }
    """
    return controller.recommend(req)
