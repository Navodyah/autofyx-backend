from __future__ import annotations

from typing import Dict, Any

import pandas as pd
import numpy as np

from schemas.recommender_schemas import RecommendRequest, RecommendResponse
from Vehicle_recommender_pipeline import DBPipelineRecommender, DB_CONFIG


# Financial Calculation Constants
DEFAULT_RATE_OF_INTEREST = 13.0
DEFAULT_MONTHS = 60
DEFAULT_DOWN_PAYMENT_RATIO = 0.50


def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate monthly EMI given principal, annual interest rate, and loan tenure."""
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:
        return principal / months

    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def get_salary_level(monthly_income: float | None) -> str:
    if monthly_income is None or monthly_income <= 0:
        return "medium"  # Default
    if monthly_income < 100000:
        return "low"
    if monthly_income <= 350000:
        return "medium"
    if monthly_income <= 600000:
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
    - Applies financial affordability filtering post-ranking
    """

    def __init__(self) -> None:
        self.pipeline = DBPipelineRecommender(DB_CONFIG)

    def recommend(self, req: RecommendRequest) -> RecommendResponse:
        # Extract and validate salary (required)
        monthly_income = float(req.salary)

        # Finance parameters with defaults
        rate_of_interest = float(req.rate_of_interest) if req.rate_of_interest is not None else DEFAULT_RATE_OF_INTEREST
        number_of_months = int(req.number_of_months) if req.number_of_months is not None else DEFAULT_MONTHS
        down_payment_ratio = float(req.down_payment_ratio) if req.down_payment_ratio is not None else DEFAULT_DOWN_PAYMENT_RATIO
        user_down_payment_amount = float(req.down_payment_amount) if req.down_payment_amount is not None else None

        # Maximum EMI user can afford (40% of salary)
        max_monthly_emi = monthly_income * 0.4

        # For response metadata
        salary_level = req.salary_level or get_salary_level(monthly_income)
        usage_area = (req.area or "mixed").strip().lower()
        normalized_vehicle_class = str(req.vehicle_class).strip() if req.vehicle_class else None
        safe_top_n = max(1, min(int(req.top_n), 50))
        safe_candidate_limit = max(safe_top_n, int(req.candidate_limit))
        
        # Fetch more candidates to allow post-filtering by affordability
        prefilter_top_n = min(max(safe_top_n * 5, safe_top_n), 50)

        # Build user profile for pipeline
        user_profile: Dict[str, Any] = {
            "monthly_income": monthly_income,
            "salary_level": salary_level,
            "primary_need": get_primary_need(req.purpose),
            "usage": usage_area,
            "max_fuel_consumption": req.max_comb_l_per_100,
            "fuel": req.fuel,
            "transmission": req.transmission,
            "vehicle_class": normalized_vehicle_class,
        }

        # Remove None values from profile
        user_profile = {k: v for k, v in user_profile.items() if v is not None}

        # Run pipeline to get requirement-ranked candidates
        df: pd.DataFrame = self.pipeline.recommend(
            user_profile=user_profile,
            top_n=prefilter_top_n,
            candidate_limit=safe_candidate_limit,
        )
        df = df.replace({np.nan: None})

        # Check for error message from pipeline
        if "message" in df.columns and len(df.columns) == 1:
            msg = str(df.iloc[0]["message"])
            return RecommendResponse(
                message=msg,
                count=0,
                items=[],
                finance={
                    "salary": monthly_income,
                    "rate_of_interest": rate_of_interest,
                    "number_of_months": number_of_months,
                    "down_payment_amount": user_down_payment_amount,
                    "down_payment_ratio": down_payment_ratio,
                    "max_monthly_emi": max_monthly_emi,
                },
            )

        # Helper to safely convert to float
        def _to_float(value: Any) -> float | None:
            try:
                if value is None:
                    return None
                return float(value)
            except (TypeError, ValueError):
                return None

        # Financial filtering: calculate EMI for each vehicle and keep only affordable ones
        affordable_items = []

        for item in df.to_dict(orient="records"):
            min_price = _to_float(item.get("minimum_price"))
            max_price_value = _to_float(item.get("max_price"))

            # Skip if both prices are missing
            if min_price is None and max_price_value is None:
                continue

            # Fallback: use available price
            if min_price is None:
                min_price = max_price_value
            if max_price_value is None:
                max_price_value = min_price

            # Calculate average vehicle price
            average_price = (float(min_price) + float(max_price_value)) / 2.0
            item["average_price"] = average_price

            # Calculate down payment: use user's absolute amount if provided, else use ratio
            if user_down_payment_amount is not None:
                # User provided absolute down payment in LKR
                down_payment_amount = user_down_payment_amount
            else:
                # Use ratio-based calculation (default 50% of vehicle price)
                down_payment_amount = average_price * down_payment_ratio
            item["down_payment_amount"] = down_payment_amount

            # Calculate loan principal: vehicle price minus down payment
            loan_principal = average_price - down_payment_amount
            item["loan_principal"] = loan_principal

            # Calculate monthly EMI
            monthly_emi = calculate_emi(loan_principal, rate_of_interest, number_of_months)
            item["monthly_emi"] = monthly_emi

            # Total repayable amount over the full tenure, including interest
            total_payable_amount = monthly_emi * number_of_months
            total_interest_amount = total_payable_amount - loan_principal
            item["total_payable_amount"] = total_payable_amount
            item["total_interest_amount"] = total_interest_amount

            # Check affordability: EMI must be <= 40% of salary
            is_affordable = monthly_emi <= max_monthly_emi
            item["is_affordable"] = is_affordable
            item["emi_vs_salary_percent"] = (monthly_emi / monthly_income) * 100.0 if monthly_income > 0 else 0.0

            # Keep only affordable vehicles
            if is_affordable:
                affordable_items.append(item)

        # Limit to requested top_n
        affordable_items = affordable_items[:safe_top_n]

        # Response with finance metadata
        if not affordable_items:
            return RecommendResponse(
                message="No vehicles matched both your requirements and financial affordability (EMI <= 40% of salary).",
                count=0,
                items=[],
            finance={
                "salary": monthly_income,
                "rate_of_interest": rate_of_interest,
                "number_of_months": number_of_months,
                "down_payment_amount": user_down_payment_amount,
                "down_payment_ratio": down_payment_ratio,
                "max_monthly_emi": max_monthly_emi,
                "reason": "No vehicles could be financed within your EMI budget",
            },
            )

        return RecommendResponse(
            message=f"Found {len(affordable_items)} recommendations matching your requirements and financial situation.",
            count=len(affordable_items),
            items=affordable_items,
            finance={
                "salary": monthly_income,
                "rate_of_interest": rate_of_interest,
                "number_of_months": number_of_months,
                "down_payment_amount": user_down_payment_amount,
                "down_payment_ratio": down_payment_ratio,
                "max_monthly_emi": max_monthly_emi,
                "note": f"Showing only vehicles where monthly EMI is at most {max_monthly_emi:.0f} LKR (40% of your salary). Each item also includes total_payable_amount and total_interest_amount.",
            },
        )

