from __future__ import annotations

from typing import Dict, Any

import pandas as pd

import numpy as np

from schemas.recommender_schemas import RecommendRequest, RecommendResponse

# Import your pipeline wrapper from vehicle_recommender_pipeline.py
from Vehicle_recommender_pipeline import DBPipelineRecommender, DB_CONFIG


def get_salary_level(monthly_income: float | None) -> str:
    if monthly_income is None:
        return "medium"  # Default
    if monthly_income <= 80000:
        return "low"
    if monthly_income <= 250000:
        return "medium"
    if monthly_income <= 700000:
        return "high"
    return "luxury"


def get_primary_need(purpose: str) -> str:
    purpose_map = {
        "daily_commute": "economy",
        "family": "family",
        "performance": "performance",
        "luxury": "luxury",
    }
    return purpose_map.get(purpose.lower(), "economy")


class RecommendationController:
    """
    Controller layer:
    - Keeps pipeline instance (loads models + lookup cache once)
    - Converts request -> pipeline inputs -> response JSON
    """

    def __init__(self) -> None:
        self.pipeline = DBPipelineRecommender(DB_CONFIG)

    def recommend(self, req: RecommendRequest) -> RecommendResponse:
        # Determine salary level
        salary_level = req.salary_level or get_salary_level(req.monthly_income)

        # Build dict for ML pipeline
        user_profile: Dict[str, Any] = {
            "salary_level": salary_level,
            "primary_need": get_primary_need(req.purpose),
            "usage": req.area.lower(),
            "max_fuel_consumption": req.max_comb_l_per_100,
        }

        # Remove None values from profile
        user_profile = {k: v for k, v in user_profile.items() if v is not None}

        # Run pipeline
        df: pd.DataFrame = self.pipeline.recommend(
            user_profile=user_profile,
            top_n=req.top_n,
            candidate_limit=req.candidate_limit,
        )
        df = df.replace({np.nan: None})

        # Pipeline may return a message
        if "message" in df.columns and len(df.columns) == 1:
            msg = str(df.iloc[0]["message"])
            return RecommendResponse(message=msg, count=0, items=[])

        # Convert to JSON list
        items = df.to_dict(orient="records")
        return RecommendResponse(message=f"Found {len(items)} recommendations.", count=len(items), items=items)
