from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict, List

from controllers.recommender_controller import RecommendationController
from schemas.recommender_schemas import RecommendRequest, RecommendResponse
from services.recommendation_history_service import (
    save_recommendation_history,
    track_top3_vehicle_scores,
    get_recommendation_history,
    get_vehicle_leaderboard,
    get_global_recommendation_timeline,
)

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


# ── History & Scoring Routes ────────────────────────────────────────────────

@router.post("/save-history")
def save_history(body: Dict[str, Any] = Body(...)):
    """
    Save up to 15 recommended vehicles in the user's recommendation history.
    Body: { "user_id": str, "vehicles": [ {...}, ... ] }
    """
    try:
        user_id  = body.get("user_id", "")
        vehicles = body.get("vehicles", [])
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required.")
        return save_recommendation_history(user_id, vehicles)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-scores")
def track_scores(body: Dict[str, Any] = Body(...)):
    """
    Increment recommendation_count for the top-3 vehicles (global analytics).
    Body: { "vehicles": [ {...}, {...}, {...} ] }
    """
    try:
        vehicles = body.get("vehicles", [])
        return track_top3_vehicle_scores(vehicles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
def fetch_history(user_id: str):
    """Fetch the stored recommendation history for a specific user."""
    try:
        return get_recommendation_history(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
def vehicle_leaderboard(limit: int = 20):
    """Return top-N vehicles ranked by cumulative recommendation count."""
    try:
        return get_vehicle_leaderboard(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
def global_timeline():
    """Return a time-series of total global recommendation activity."""
    try:
        return get_global_recommendation_timeline()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

