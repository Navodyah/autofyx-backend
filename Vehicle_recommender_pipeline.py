from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd
from psycopg2.extras import RealDictCursor

from config.postgresql import get_postgres_connection
from services.salary_category_mapper import (
    expand_categories_for_db_filter,
    resolve_salary_vehicle_categories,
)

BASE_DIR = Path(__file__).resolve().parent
DB_CONFIG: Dict[str, Any] = {
    "models_path": BASE_DIR / "ml" / "vehicle_ranking_models.pkl",
    "metadata_path": BASE_DIR / "ml" / "vehicle_training_metadata.pkl",
    "default_candidate_limit": 2000,
    "max_candidate_limit": 20_000,
}

TARGET_COLUMNS = (
    "economy_score",
    "performance_score",
    "luxury_score",
    "family_score",
    "city_score",
    "highway_score",
    "offroad_score",
)


@lru_cache(maxsize=1)
def _load_artifacts(models_path: str, metadata_path: str):
    models = joblib.load(models_path)
    metadata = joblib.load(metadata_path)
    return models, metadata


def _usage_area_weights(area: str) -> Dict[str, float]:
    area_key = str(area or "mixed").strip().lower()
    if area_key == "city":
        return {
            "city_score": 0.65,
            "economy_score": 0.25,
            "family_score": 0.10,
        }
    if area_key == "highway":
        return {
            "highway_score": 0.55,
            "performance_score": 0.30,
            "economy_score": 0.15,
        }
    if area_key in {"off-road", "offroad"}:
        return {
            "offroad_score": 0.70,
            "performance_score": 0.20,
            "family_score": 0.10,
        }
    return {
        "city_score": 0.30,
        "highway_score": 0.30,
        "family_score": 0.20,
        "economy_score": 0.20,
    }


def _primary_need_weights(primary_need: str) -> Dict[str, float]:
    need_key = str(primary_need or "economy").strip().lower()
    if need_key == "family":
        return {
            "family_score": 0.55,
            "economy_score": 0.20,
            "city_score": 0.15,
            "highway_score": 0.10,
        }
    if need_key == "performance":
        return {
            "performance_score": 0.65,
            "highway_score": 0.20,
            "luxury_score": 0.15,
        }
    if need_key == "luxury":
        return {
            "luxury_score": 0.60,
            "performance_score": 0.20,
            "highway_score": 0.10,
            "family_score": 0.10,
        }
    return {
        "economy_score": 0.55,
        "city_score": 0.25,
        "family_score": 0.20,
    }


def _build_target_weights(primary_need: str, area: str) -> Dict[str, float]:
    weights = {col: 0.0 for col in TARGET_COLUMNS}

    for target, value in _primary_need_weights(primary_need).items():
        weights[target] += value * 0.65

    for target, value in _usage_area_weights(area).items():
        weights[target] += value * 0.35

    total = sum(weights.values())
    if total <= 0:
        return {"family_score": 0.5, "economy_score": 0.5}

    return {target: value / total for target, value in weights.items() if value > 0}


def _normalize_token(value: str) -> str:
    return str(value or "").strip().upper().replace("_", " ")


def _fuel_search_token(fuel_value: str) -> str:
    token = _normalize_token(fuel_value)
    mapping = {
        "X": "REGULAR",
        "Z": "PREMIUM",
        "D": "DIESEL",
        "E": "ELECTRIC",
    }
    return mapping.get(token, token)


def _fuel_filter_terms(fuel_value: str) -> Dict[str, str]:
    raw = _normalize_token(fuel_value)
    mapped = _fuel_search_token(raw)
    return {
        "token": raw,
        "mapped": mapped,
    }


def _transmission_search_token(transmission_value: str) -> str:
    token = _normalize_token(transmission_value)
    mapping = {
        "A": "AUTO",
        "AUTOMATIC": "AUTO",
        "MANUAL": "MANUAL",
    }
    return mapping.get(token, token)


def _transmission_filter_terms(transmission_value: str) -> Dict[str, str]:
    raw = _normalize_token(transmission_value)
    mapped = _transmission_search_token(raw)
    return {
        "token": raw,
        "mapped": mapped,
    }


def _build_db_filters(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    monthly_income = user_profile.get("monthly_income")
    salary_level = user_profile.get("salary_level")
    explicit_vehicle_class = user_profile.get("vehicle_class")

    salary_categories = resolve_salary_vehicle_categories(
        monthly_income=_safe_float(monthly_income),
        salary_level=str(salary_level) if salary_level is not None else None,
        validate_positive=False,
    )
    salary_class_filters = (
        expand_categories_for_db_filter(salary_categories) if salary_categories else []
    )

    explicit_class_filters = []
    if explicit_vehicle_class:
        explicit_class_filters = expand_categories_for_db_filter([str(explicit_vehicle_class)])

    # Salary affordability is the primary filter; explicit class narrows it further.
    if salary_class_filters and explicit_class_filters:
        class_filters = sorted(set(salary_class_filters).intersection(explicit_class_filters))
    elif salary_class_filters:
        class_filters = salary_class_filters
    else:
        class_filters = explicit_class_filters

    max_comb = user_profile.get("max_fuel_consumption")
    max_comb_numeric = float(max_comb) if max_comb is not None else None

    return {
        "class_filters": class_filters,
        "max_comb": max_comb_numeric,
        "fuel": user_profile.get("fuel"),
        "transmission": user_profile.get("transmission"),
        "selected_categories": salary_categories,
    }


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_candidate_query(
    user_profile: Dict[str, Any],
    filters: Dict[str, Any],
    candidate_limit: int,
) -> tuple[str, Dict[str, Any]]:
    query_parts = [
        """
        SELECT
            v.vehicle_id AS vehicle_id,
            v.manufacturing_year AS \"YEAR\",
            b.brand_name AS \"Make\",
            v.model_name AS \"Model\",
            c.class_name AS \"VEHICLE CLASS\",
            (v.minimum_price::float * 1000000) AS minimum_price,
            (v.max_price::float * 1000000) AS max_price,
            v.engine_size::float AS \"ENGINE SIZE\",
            GREATEST(3, ROUND(COALESCE(v.engine_size::float, 1.0) * 2))::float AS \"CYLINDERS\",
            t.transmission_name AS \"Transmission\",
            f.fuel_type_name AS \"FUEL\",
            et.engine_type_name AS \"ENGINE TYPE\",
            CASE
                WHEN v.fuel_efficiency_combined IS NOT NULL THEN v.fuel_efficiency_combined::float
                WHEN v.fuel_efficiency_highway IS NOT NULL THEN (v.fuel_efficiency_highway::float * 1.15)
                ELSE NULL
            END AS \"CITY (L/100 km)\",
            v.fuel_efficiency_highway::float AS \"HWY (L/100 km)\",
            v.fuel_efficiency_combined::float AS \"COMB (L/100 km)\",
            CASE
                WHEN v.fuel_efficiency_combined IS NOT NULL AND v.fuel_efficiency_combined > 0
                    THEN 235.215 / v.fuel_efficiency_combined::float
                ELSE NULL
            END AS \"COMB (mpg)\",
            CASE
                WHEN v.fuel_efficiency_combined IS NOT NULL THEN v.fuel_efficiency_combined::float * 23.0
                ELSE NULL
            END AS \"EMISSIONS\",
            mc.record_id AS maintenance_record_id,
            mc.yearly_cost::float AS maintenance_yearly_cost,
            mc.recorded_date AS maintenance_recorded_date,
            mc.source AS maintenance_source
        FROM vehicles v
        JOIN brands b ON b.brand_id = v.brand_id
        LEFT JOIN vehicle_classes c ON c.class_id = v.class_id
        LEFT JOIN engine_types et ON et.engine_type_id = v.engine_type_id
        LEFT JOIN transmissions t ON t.transmission_id = v.transmission_id
        LEFT JOIN fuel_types f ON f.fuel_type_id = v.fuel_type_id
        LEFT JOIN LATERAL (
            SELECT
                m.record_id,
                m.yearly_cost,
                m.recorded_date,
                m.source
            FROM maintenance_costs m
            WHERE m.vehicle_id = v.vehicle_id
            ORDER BY m.recorded_date DESC NULLS LAST, m.record_id DESC
            LIMIT 1
        ) mc ON TRUE
        WHERE v.manufacturing_year IS NOT NULL
        """
    ]

    params: Dict[str, Any] = {"candidate_limit": candidate_limit}

    if filters["max_comb"] is not None:
        query_parts.append("AND v.fuel_efficiency_combined::float <= %(max_comb)s")
        params["max_comb"] = filters["max_comb"]

    class_filters = filters["class_filters"]
    if class_filters:
        query_parts.append("AND UPPER(REPLACE(COALESCE(c.class_name, ''), '_', ' ')) = ANY(%(class_filters)s)")
        params["class_filters"] = class_filters

    fuel = user_profile.get("fuel")
    if fuel:
        fuel_terms = _fuel_filter_terms(str(fuel))
        query_parts.append(
            """
            AND (
                UPPER(COALESCE(f.fuel_type_name, '')) = %(fuel_token)s
                OR UPPER(COALESCE(f.fuel_type_name, '')) = %(fuel_mapped)s
                OR UPPER(COALESCE(f.fuel_type_name, '')) LIKE %(fuel_token_like)s
                OR UPPER(COALESCE(f.fuel_type_name, '')) LIKE %(fuel_mapped_like)s
            )
            """
        )
        params["fuel_token"] = fuel_terms["token"]
        params["fuel_mapped"] = fuel_terms["mapped"]
        params["fuel_token_like"] = f"%{fuel_terms['token']}%"
        params["fuel_mapped_like"] = f"%{fuel_terms['mapped']}%"

    transmission = user_profile.get("transmission")
    if transmission:
        transmission_terms = _transmission_filter_terms(str(transmission))
        query_parts.append(
            """
            AND (
                UPPER(COALESCE(t.transmission_name, '')) = %(transmission_token)s
                OR UPPER(COALESCE(t.transmission_name, '')) = %(transmission_mapped)s
                OR UPPER(COALESCE(t.transmission_name, '')) LIKE %(transmission_token_like)s
                OR UPPER(COALESCE(t.transmission_name, '')) LIKE %(transmission_mapped_like)s
            )
            """
        )
        params["transmission_token"] = transmission_terms["token"]
        params["transmission_mapped"] = transmission_terms["mapped"]
        params["transmission_token_like"] = f"%{transmission_terms['token']}%"
        params["transmission_mapped_like"] = f"%{transmission_terms['mapped']}%"

    query_parts.append("ORDER BY v.manufacturing_year DESC, v.vehicle_id DESC")
    query_parts.append("LIMIT %(candidate_limit)s")

    return "\n".join(query_parts), params


def fetch_vehicle_data_from_postgres(
    user_profile: Dict[str, Any],
    candidate_limit: int = 2000,
) -> pd.DataFrame:
    """
    Fetch recommendation candidates from PostgreSQL using salary and user filters.
    This function can be used independently before ML ranking when needed.
    """
    safe_limit = max(1, int(candidate_limit))
    filters = _build_db_filters(user_profile)
    sql, params = _build_candidate_query(
        user_profile=user_profile,
        filters=filters,
        candidate_limit=safe_limit,
    )

    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return pd.DataFrame(rows)


class DBPipelineRecommender:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        cfg = dict(DB_CONFIG)
        if config:
            cfg.update(config)
        self.config = cfg

        models_path = str(cfg["models_path"])
        metadata_path = str(cfg["metadata_path"])
        self.models, self.metadata = _load_artifacts(models_path, metadata_path)
        self.feature_columns = list(self.metadata.get("all_feature_columns", []))

    def _fetch_candidates(self, user_profile: Dict[str, Any], candidate_limit: int) -> pd.DataFrame:
        return fetch_vehicle_data_from_postgres(
            user_profile=user_profile,
            candidate_limit=candidate_limit,
        )

    def _fetch_candidates_with_fallback(
        self,
        user_profile: Dict[str, Any],
        candidate_limit: int,
    ) -> pd.DataFrame:
        candidates_df = self._fetch_candidates(user_profile=user_profile, candidate_limit=candidate_limit)
        if not candidates_df.empty:
            return candidates_df

        # Relax optional hard filters gradually, but keep salary affordability constraints.
        relaxed_profile = dict(user_profile)
        relaxation_order = ["fuel", "transmission", "max_fuel_consumption", "vehicle_class"]

        for key in relaxation_order:
            if key not in relaxed_profile:
                continue
            relaxed_profile.pop(key, None)
            candidates_df = self._fetch_candidates(
                user_profile=relaxed_profile,
                candidate_limit=candidate_limit,
            )
            if not candidates_df.empty:
                return candidates_df

        return candidates_df

    def _prepare_features(self, candidates_df: pd.DataFrame) -> pd.DataFrame:
        from ml.recommend_vehicle_s import standardize_input

        prepared_df = standardize_input(candidates_df)

        for feature in self.feature_columns:
            if feature not in prepared_df.columns:
                prepared_df[feature] = 0.0

        return prepared_df

    def recommend(
        self,
        user_profile: Dict[str, Any],
        top_n: int = 10,
        candidate_limit: int = 2000,
    ) -> pd.DataFrame:
        safe_top_n = max(1, min(int(top_n), 50))
        max_limit = int(self.config.get("max_candidate_limit", 20_000))
        safe_limit = max(safe_top_n, min(int(candidate_limit), max_limit))

        candidates_df = self._fetch_candidates_with_fallback(
            user_profile=user_profile,
            candidate_limit=safe_limit,
        )
        if candidates_df.empty:
            return pd.DataFrame(
                [{"message": "No vehicles matched the salary and filter constraints."}]
            )

        prepared_df = self._prepare_features(candidates_df.copy())
        feature_df = prepared_df[self.feature_columns].copy()

        scored_df = prepared_df.copy()
        for target, model in self.models.items():
            scored_df[target] = model.predict(feature_df)

        weights = _build_target_weights(
            primary_need=str(user_profile.get("primary_need", "economy")),
            area=str(user_profile.get("usage", "mixed")),
        )

        scored_df["raw_compatibility_score"] = 0.0
        for target, weight in weights.items():
            if target in scored_df.columns:
                scored_df["raw_compatibility_score"] += scored_df[target] * float(weight)

        max_raw = _safe_float(scored_df["raw_compatibility_score"].max(), 0.0) or 0.0
        if max_raw > 0:
            scored_df["Compatibility_Score"] = (scored_df["raw_compatibility_score"] / max_raw) * 100.0
        else:
            scored_df["Compatibility_Score"] = 0.0

        scored_df["Need_Match"] = scored_df["Compatibility_Score"]

        usage_targets = {
            "city": "city_score",
            "highway": "highway_score",
            "off-road": "offroad_score",
            "offroad": "offroad_score",
            "mixed": "family_score",
        }
        usage_key = str(user_profile.get("usage", "mixed")).strip().lower()
        usage_target = usage_targets.get(usage_key, "family_score")
        if usage_target in scored_df.columns:
            usage_max = _safe_float(scored_df[usage_target].max(), 0.0) or 0.0
            if usage_max > 0:
                scored_df["Usage_Match"] = (scored_df[usage_target] / usage_max) * 100.0
            else:
                scored_df["Usage_Match"] = 0.0
        else:
            scored_df["Usage_Match"] = 0.0

        display_columns = [
            "vehicle_id",
            "YEAR",
            "Make",
            "Model",
            "VEHICLE CLASS",
            "minimum_price",
            "max_price",
            "ENGINE SIZE",
            "CYLINDERS",
            "Transmission",
            "FUEL",
            "COMB (L/100 km)",
            "COMB (mpg)",
            "EMISSIONS",
            "maintenance_record_id",
            "maintenance_yearly_cost",
            "maintenance_recorded_date",
            "maintenance_source",
            "Compatibility_Score",
            "Need_Match",
            "Usage_Match",
        ]
        available_display_columns = [c for c in display_columns if c in scored_df.columns]

        ranked = (
            scored_df.sort_values("raw_compatibility_score", ascending=False)
            .head(safe_top_n)
            .copy()
        )

        return ranked[available_display_columns].reset_index(drop=True)
