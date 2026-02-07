from __future__ import annotations

from typing import Dict, Any

import pandas as pd

from schemas.recommender_schemas import RecommendRequest, RecommendResponse

# Import your pipeline wrapper from vehicle_recommendation_pipeline.py
from Vehicle_recommendation_pipeline import DBPipelineRecommender, DB_CONFIG


class RecommendationController:
    """
    Controller layer:
    - Keeps pipeline instance (loads models + lookup cache once)
    - Converts request -> pipeline inputs -> response JSON
    """

    def __init__(self) -> None:
        self.pipeline = DBPipelineRecommender(DB_CONFIG)

    def recommend(self, req: RecommendRequest) -> RecommendResponse:
        # Build dict for pipeline
        user_input: Dict[str, Any] = {
            "monthly_income": req.monthly_income,
            "salary_level": req.salary_level,   # optional override
            "purpose": req.purpose,
            "area": req.area,
            "fuel": req.fuel,
            "transmission": req.transmission,
            "max_comb_l_per_100": req.max_comb_l_per_100,
            "vehicle_class": req.vehicle_class,
        }

        # Remove None values
        user_input = {k: v for k, v in user_input.items() if v is not None}

        # Run pipeline
        df: pd.DataFrame = self.pipeline.recommend(
            user_input=user_input,
            top_n=req.top_n,
            candidate_limit=req.candidate_limit,
        )

        # Pipeline may return message-only df
        if "message" in df.columns and len(df.columns) == 1:
            msg = str(df.iloc[0]["message"])
            return RecommendResponse(message=msg, count=0, items=[])

        # Convert to JSON list
        items = df.to_dict(orient="records")
        return RecommendResponse(message=None, count=len(items), items=items)
