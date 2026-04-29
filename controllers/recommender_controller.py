from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

# ── Ensure the project root is on sys.path so the pipeline
#    module and its sub-imports (ml.recommend_vehicle_s, services, config)
#    resolve correctly regardless of working directory. ──────────────────────
_API_ROOT = Path(__file__).resolve().parent.parent  # controllers/ → api/
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from Vehicle_recommender_pipeline import DB_CONFIG, DBPipelineRecommender  # noqa: E402
from schemas.recommender_schemas import RecommendRequest, RecommendResponse  # noqa: E402

# ── Financial Calculation Constants ───────────────────────────────────────────
DEFAULT_RATE_OF_INTEREST = 13.0
DEFAULT_MONTHS = 60
DEFAULT_DOWN_PAYMENT_RATIO = 0.50


# ── Helpers ───────────────────────────────────────────────────────────────────

def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Calculate monthly EMI given principal, annual interest rate, and loan tenure."""
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:
        return principal / months

    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def get_salary_level(monthly_income: float | None) -> str:
    """
    Sri Lanka 4-tier income classification.
    Aligned with SALARY_VEHICLE_CATEGORY_RULES in salary_category_mapper.py.
    """
    if monthly_income is None or monthly_income <= 0:
        return "medium"  # safe default
    if monthly_income < 100_000:
        return "low"          # KEI / MINICOMPACT / SUBCOMPACT
    if monthly_income < 250_000:
        return "medium_low"   # SUBCOMPACT / COMPACT / WAGON
    if monthly_income <= 600_000:
        return "medium"       # COMPACT / MID - SIZE / MPV / SUV - SMALL
    if monthly_income <= 1_000_000:
        return "high"         # MID - SIZE / FULL - SIZE / SUV / OFF - ROAD
    return "luxury"           # FULL - SIZE / all classes


def get_primary_need(purpose: str) -> str:
    purpose_map = {
        "daily_commute": "economy",
        "family": "family",
        "performance": "performance",
        "luxury": "luxury",
    }
    return purpose_map.get(purpose.lower(), "economy")


# ── Controller ────────────────────────────────────────────────────────────────

class RecommendationController:
    """
    Controller layer:
    - Keeps pipeline instance (loads ML models + lookup cache once via lazy init)
    - Converts request → pipeline inputs → response JSON
    - Applies financial affordability filtering post-ranking

    The pipeline references:
      ml/vehicle_ranking_models_past.pkl        (237 MB XGBoost ensemble)
      ml/vehicle_training_metadata_past.pkl     (feature column list)
    Both paths are resolved relative to Vehicle_recommender_pipeline.py using
    Path(__file__).resolve().parent, so they are always absolute and CWD-safe.
    """

    def __init__(self) -> None:
        self._pipeline: DBPipelineRecommender | None = None
        self._init_error: str | None = None

        # Eagerly load the pipeline so startup failures surface immediately.
        try:
            self._pipeline = DBPipelineRecommender(DB_CONFIG)
        except Exception as exc:  # noqa: BLE001
            self._init_error = (
                f"ML pipeline failed to initialise. "
                f"Verify that ml/vehicle_ranking_models_past.pkl and "
                f"ml/vehicle_training_metadata_past.pkl exist under {_API_ROOT}. "
                f"Detail: {exc}"
            )

    # ── Public API ──────────────────────────────────────────────────────────

    def recommend(self, req: RecommendRequest) -> RecommendResponse:
        # Surface pipeline init error as a structured response
        if self._pipeline is None:
            return RecommendResponse(
                message=self._init_error or "ML pipeline not initialised.",
                count=0,
                items=[],
                finance={},
            )

        # ── Parse financial inputs ──────────────────────────────────────────
        monthly_income = float(req.salary)
        rate_of_interest = (
            float(req.rate_of_interest)
            if req.rate_of_interest is not None
            else DEFAULT_RATE_OF_INTEREST
        )
        number_of_months = (
            int(req.number_of_months)
            if req.number_of_months is not None
            else DEFAULT_MONTHS
        )
        down_payment_ratio = (
            float(req.down_payment_ratio)
            if req.down_payment_ratio is not None
            else DEFAULT_DOWN_PAYMENT_RATIO
        )
        user_down_payment_amount = (
            float(req.down_payment_amount) if req.down_payment_amount is not None else None
        )

        # Max EMI the user can afford (60 % of monthly salary)
        max_monthly_emi = monthly_income * 0.6

        # Derived metadata
        salary_level = req.salary_level or get_salary_level(monthly_income)
        usage_area = (req.area or "mixed").strip().lower()
        normalized_vehicle_class = (
            str(req.vehicle_class).strip() if req.vehicle_class else None
        )
        safe_top_n = max(1, min(int(req.top_n), 50))
        safe_candidate_limit = max(safe_top_n, int(req.candidate_limit))

        # Fetch more candidates to allow post-filtering by affordability
        prefilter_top_n = min(max(safe_top_n * 5, safe_top_n), 50)

        # ── Build user profile for the ML pipeline ──────────────────────────
        user_profile: Dict[str, Any] = {
            "monthly_income": monthly_income,
            "salary_level": salary_level,
            "primary_need": get_primary_need(req.purpose),
            "usage": usage_area,
            "max_fuel_consumption": req.max_comb_l_per_100,
            "fuel": req.fuel,
            "transmission": req.transmission,
            "vehicle_class": normalized_vehicle_class,
            # Frontend pre-computed class list (salary ∩ purpose × area).
            # When present this takes priority over all internal class mapper logic.
            "vehicle_classes": (
                [c.strip() for c in req.vehicle_classes if c.strip()]
                if req.vehicle_classes
                else None
            ),
            "maintainability": req.maintainability_priority,
        }
        # Strip None values so the pipeline's fallback logic works correctly
        user_profile = {k: v for k, v in user_profile.items() if v is not None}

        # ── Run ML pipeline ────────────────────────────────────────────────
        #   DBPipelineRecommender loads models from:
        #     DB_CONFIG["models_path"]   = <api_root>/ml/vehicle_ranking_models_past.pkl
        #     DB_CONFIG["metadata_path"] = <api_root>/ml/vehicle_training_metadata_past.pkl
        df: pd.DataFrame = self._pipeline.recommend(
            user_profile=user_profile,
            top_n=prefilter_top_n,
            candidate_limit=safe_candidate_limit,
        )
        df = df.replace({np.nan: None})

        # Pipeline returns a single-column "message" frame on no results
        if "message" in df.columns and len(df.columns) == 1:
            return RecommendResponse(
                message=str(df.iloc[0]["message"]),
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

        # ── Financial affordability filtering ──────────────────────────────
        def _to_float(value: Any) -> float | None:
            try:
                return None if value is None else float(value)
            except (TypeError, ValueError):
                return None

        affordable_items = []

        for item in df.to_dict(orient="records"):
            min_price = _to_float(item.get("minimum_price"))
            max_price_value = _to_float(item.get("max_price"))

            # Skip vehicles with no price data
            if min_price is None and max_price_value is None:
                continue

            # Fallback: use whichever price is available
            if min_price is None:
                min_price = max_price_value
            if max_price_value is None:
                max_price_value = min_price

            average_price = (float(min_price) + float(max_price_value)) / 2.0
            item["average_price"] = average_price

            # Down payment: absolute amount overrides ratio
            if user_down_payment_amount is not None:
                down_payment_amount = user_down_payment_amount
            else:
                down_payment_amount = average_price * down_payment_ratio
            item["down_payment_amount"] = down_payment_amount

            # Loan principal
            loan_principal = average_price - down_payment_amount
            item["loan_principal"] = loan_principal

            # Monthly EMI
            monthly_emi = calculate_emi(loan_principal, rate_of_interest, number_of_months)
            item["monthly_emi"] = monthly_emi

            # Total cost of credit
            total_payable_amount = monthly_emi * number_of_months
            total_interest_amount = total_payable_amount - loan_principal
            item["total_payable_amount"] = total_payable_amount
            item["total_interest_amount"] = total_interest_amount

            # Affordability flag
            is_affordable = monthly_emi <= max_monthly_emi
            item["is_affordable"] = is_affordable
            item["emi_vs_salary_percent"] = (
                (monthly_emi / monthly_income) * 100.0 if monthly_income > 0 else 0.0
            )

            if is_affordable:
                affordable_items.append(item)

        # Limit to requested top_n
        affordable_items = affordable_items[:safe_top_n]

        # ── Build response ─────────────────────────────────────────────────
        finance_meta: Dict[str, Any] = {
            "salary": monthly_income,
            "rate_of_interest": rate_of_interest,
            "number_of_months": number_of_months,
            "down_payment_amount": user_down_payment_amount,
            "down_payment_ratio": down_payment_ratio,
            "max_monthly_emi": max_monthly_emi,
        }

        if not affordable_items:
            return RecommendResponse(
                message=(
                    "No vehicles matched both your requirements and financial "
                    "affordability (EMI ≤ 60 % of salary)."
                ),
                count=0,
                items=[],
                finance={
                    **finance_meta,
                    "reason": "No vehicles could be financed within your EMI budget",
                },
            )

        return RecommendResponse(
            message=(
                f"Found {len(affordable_items)} recommendations matching your "
                "requirements and financial situation."
            ),
            count=len(affordable_items),
            items=affordable_items,
            finance={
                **finance_meta,
                "note": (
                    f"Showing only vehicles where monthly EMI ≤ "
                    f"{max_monthly_emi:,.0f} LKR (60 % of salary). "
                    "Each item includes monthly_emi, total_payable_amount, "
                    "and total_interest_amount."
                ),
            },
        )
