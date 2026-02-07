from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
import psycopg2

# Your existing ML recommender (CSV-based) class
from vehicle_recommender import VehicleRecommender


# =========================
# 1) DB CONFIG
# =========================
# ⚠️ Security note: In production, DO NOT hardcode passwords.
# Use env vars (recommended): export DB_PASSWORD="..."
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "autofyx-autofyx.l.aivencloud.com"),
    "port": int(os.getenv("DB_PORT", "17459")),
    "database": os.getenv("DB_NAME", "autofyx"),
    "user": os.getenv("DB_USER", "avnadmin"),
    # If you still want to hardcode, replace the getenv with your password.
    "password": os.getenv("DB_PASSWORD", "AVNS_2AEJXab9YDAGyXW6vas"),
}


# =========================
# 2) Helpers
# =========================
def norm_text(x: Any) -> Optional[str]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip().upper()
    s = s.replace(":", " - ").replace("_", " ")
    s = " ".join(s.split())
    return s


def first_letter(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip().upper()
    return s[0] if s else None


def l_per_100_to_mpg(l: Optional[float]) -> Optional[float]:
    if l is None or pd.isna(l) or l <= 0:
        return None
    return 235.214583 / float(l)


def parse_cylinders(engine_type_name: Optional[str]) -> Optional[int]:
    """engine_type_name like 'I4', 'V6', 'V8', etc."""
    if not engine_type_name:
        return None
    m = re.search(r"([IV])\s*(\d+)", str(engine_type_name).strip().upper())
    if m:
        return int(m.group(2))
    return None


def trans_category(trans_name: Optional[str]) -> str:
    """
    Convert transmission like 'A6', 'AM7', 'AS6', 'AV' into model category:
    'A', 'AM', 'AS', 'AV', 'M'
    """
    if not trans_name:
        return "Unknown"
    t = str(trans_name).strip().upper()
    for pref in ("AM", "AS", "AV"):
        if t.startswith(pref):
            return pref
    if t.startswith("A"):
        return "A"
    if t.startswith("M"):
        return "M"
    return t


# ✅ NEW: monthly income -> salary_level (your rule)
def income_to_salary_level(monthly_income: Any) -> Optional[str]:
    """
    Convert user's monthly income (LKR) -> salary_level:
      <150000        => low
      150000-600000  => medium
      600000-999999  => high
      >=1000000      => luxury
    """
    if monthly_income is None:
        return None
    try:
        inc = float(monthly_income)
    except (TypeError, ValueError):
        return None

    if inc < 150000:
        return "low"
    elif 150000 <= inc <= 600000:
        return "medium"
    elif 600000 < inc < 1000000:
        return "high"
    return "luxury"


# ✅ NEW: salary_level -> preferred DB class_name list
# ⚠️ These MUST match your DB vehicle_classes.class_name values.
def salary_level_to_class_names(salary_level: str) -> List[str]:
    s = (salary_level or "").strip().lower()

    if s == "low":
        # small vehicles
        return ["MINICOMPACT", "SUBCOMPACT", "COMPACT", "KEI CAR", "WAGON"]

    if s == "medium":
        # medium vehicles
        return ["COMPACT", "MID - SIZE", "WAGON", "SUV - SMALL", "MPV"]

    if s == "high":
        # high level vehicles
        return ["MID - SIZE", "FULL - SIZE", "SUV - SMALL", "SUV - STANDARD"]

    if s == "luxury":
        # luxury vehicles
        return ["FULL - SIZE", "SUV - STANDARD", "LUXURY", "MID - SIZE"]

    return []


# =========================
# 3) Lookup cache (cached ID maps)
# =========================
@dataclass
class LookupCache:
    class_name_to_id: Dict[str, int]
    fuel_name_to_id: Dict[str, int]
    brand_name_to_id: Dict[str, int]
    transmission_name_to_id: Dict[str, int]
    engine_type_name_to_id: Dict[str, int]


def load_lookup_cache(db: Dict[str, Any]) -> LookupCache:
    """
    Loads lookup tables ONCE (cached maps).
    Adjust table/column names here if yours differ.
    """
    with psycopg2.connect(**db) as conn:
        class_df = pd.read_sql_query("SELECT class_id, class_name FROM vehicle_classes;", conn)
        fuel_df = pd.read_sql_query("SELECT fuel_type_id, fuel_type_name FROM fuel_types;", conn)
        brand_df = pd.read_sql_query("SELECT brand_id, brand_name FROM brands;", conn)
        trans_df = pd.read_sql_query("SELECT transmission_id, transmission_name FROM transmissions;", conn)
        eng_df = pd.read_sql_query("SELECT engine_type_id, engine_type_name FROM engine_types;", conn)

    class_name_to_id = {norm_text(r["class_name"]): int(r["class_id"]) for _, r in class_df.iterrows()}
    fuel_name_to_id = {norm_text(r["fuel_type_name"]): int(r["fuel_type_id"]) for _, r in fuel_df.iterrows()}
    brand_name_to_id = {norm_text(r["brand_name"]): int(r["brand_id"]) for _, r in brand_df.iterrows()}
    transmission_name_to_id = {
        norm_text(r["transmission_name"]): int(r["transmission_id"]) for _, r in trans_df.iterrows()
    }
    engine_type_name_to_id = {norm_text(r["engine_type_name"]): int(r["engine_type_id"]) for _, r in eng_df.iterrows()}

    return LookupCache(
        class_name_to_id=class_name_to_id,
        fuel_name_to_id=fuel_name_to_id,
        brand_name_to_id=brand_name_to_id,
        transmission_name_to_id=transmission_name_to_id,
        engine_type_name_to_id=engine_type_name_to_id,
    )


# =========================
# 4) Map UI -> ML profile keys
#    (NO YEAR FILTERING)
# =========================
def purpose_to_primary_need(purpose: str) -> str:
    p = norm_text(purpose) or "DAILY_COMMUTE"
    if p in ("DAILY_COMMUTE", "COMMUTE", "ECONOMY"):
        return "economy"
    if p in ("FAMILY",):
        return "family"
    if p in ("PERFORMANCE", "SPORT"):
        return "performance"
    if p in ("LUXURY",):
        return "luxury"
    return "economy"


def area_to_usage(area: str) -> str:
    a = norm_text(area) or "MIXED"
    if a in ("CITY", "URBAN"):
        return "city"
    if a in ("HIGHWAY",):
        return "highway"
    if a in ("OFF-ROAD", "OFF ROAD", "OFFROAD"):
        return "off-road"
    return "mixed"


# =========================
# 5) Logical analysis (category/class selection)
#    ✅ UPDATED: uses monthly income -> salary_level -> class filter
# =========================
def logical_class_preferences(user: Dict[str, Any], cache: LookupCache) -> List[int]:
    """
    Priority:
    1) explicit vehicle_class (if provided) -> exact filter
    2) salary_level (explicit) OR monthly_income inferred -> salary-based class filter
    3) fallback to purpose/area rules
    """

    # 1) Explicit class chosen by user
    vc = norm_text(user.get("vehicle_class"))
    if vc and vc in cache.class_name_to_id:
        return [cache.class_name_to_id[vc]]

    # 2) Salary-based class selection
    # User can pass salary_level directly OR monthly_income to infer it.
    monthly_income = user.get("monthly_income", user.get("salary_amount"))
    inferred = income_to_salary_level(monthly_income)
    salary_level = (user.get("salary_level") or inferred)

    if salary_level:
        class_names = salary_level_to_class_names(str(salary_level))
        out: List[int] = []
        for n in class_names:
            nn = norm_text(n)
            if nn in cache.class_name_to_id:
                out.append(cache.class_name_to_id[nn])
        if out:
            return out  # apply salary-based class filter

    # 3) Fallback: purpose/area rules (your original logic)
    purpose = norm_text(user.get("purpose")) or "DAILY_COMMUTE"
    area = norm_text(user.get("area")) or "MIXED"

    preferred_names: List[str] = []

    if purpose == "FAMILY":
        preferred_names = ["MID - SIZE", "SUV - SMALL", "SUV - STANDARD", "MPV", "WAGON"]
    elif purpose in ("DAILY_COMMUTE", "COMMUTE", "ECONOMY"):
        preferred_names = ["SUBCOMPACT", "COMPACT", "MINICOMPACT", "KEI CAR", "WAGON"]
    elif purpose in ("OFF-ROAD", "OFF ROAD", "OFFROAD"):
        preferred_names = ["OFF - ROAD", "SUV - STANDARD", "SUV", "SUV - SMALL"]
    elif purpose in ("PERFORMANCE", "SPORT"):
        preferred_names = ["COMPACT", "MID - SIZE", "FULL - SIZE", "SUV - SMALL"]
    elif purpose == "LUXURY":
        preferred_names = ["MID - SIZE", "FULL - SIZE", "SUV - STANDARD", "SUV - SMALL"]

    if area == "CITY":
        preferred_names = list(dict.fromkeys(preferred_names + ["SUBCOMPACT", "COMPACT", "MINICOMPACT"]))

    out = []
    for n in preferred_names:
        nn = norm_text(n)
        if nn in cache.class_name_to_id:
            out.append(cache.class_name_to_id[nn])

    return out  # may be empty -> no class constraint


def transmission_ids_from_user(transmission_input: Optional[str], cache: LookupCache) -> Optional[List[int]]:
    """
    Returns list of transmission_ids to filter, or None (no filter).
    Accepts UI patterns like "A=Automatic", "Manual", "A6", "Any"
    """
    t = norm_text(transmission_input)
    if not t or "ANY" in t:
        return None

    if "AUTOMATIC" in t or t.startswith("A"):
        prefixes = ("A", "AM", "AS", "AV")
        return [tid for name, tid in cache.transmission_name_to_id.items() if any(name.startswith(p) for p in prefixes)]

    if "MANUAL" in t or t.startswith("M"):
        return [tid for name, tid in cache.transmission_name_to_id.items() if name.startswith("M")]

    if t in cache.transmission_name_to_id:
        return [cache.transmission_name_to_id[t]]

    return None


# =========================
# 6) DB candidate fetch
#    (NO manufacturing year filtering)
# =========================
def fetch_candidates_from_db(
    db: Dict[str, Any],
    cache: LookupCache,
    user: Dict[str, Any],
    limit: int = 3000,
) -> pd.DataFrame:
    max_comb = user.get("max_comb_l_per_100")
    max_comb = float(max_comb) if max_comb is not None else None

    fuel_name = norm_text(user.get("fuel"))
    fuel_type_id = cache.fuel_name_to_id.get(fuel_name) if fuel_name else None

    class_ids = logical_class_preferences(user, cache)
    transmission_ids = transmission_ids_from_user(user.get("transmission"), cache)

    sql = """
    SELECT
        v.vehicle_id,

        v.manufacturing_year AS "YEAR",
        b.brand_name         AS "MAKE",
        v.model_name         AS "MODEL",
        c.class_name         AS "VEHICLE CLASS",

        v.engine_size        AS "ENGINE SIZE",
        et.engine_type_name  AS "ENGINE_TYPE_NAME",
        t.transmission_name  AS "TRANSMISSION_NAME",
        f.fuel_type_name     AS "FUEL_TYPE_NAME",

        v.fuel_efficiency_combined AS "COMB (L/100 km)",
        v.fuel_efficiency_highway  AS "HWY (L/100 km)",

        v.description        AS "DESCRIPTION",
        v.tyre_size          AS "TYRE SIZE"
    FROM vehicles v
    JOIN brands b          ON b.brand_id = v.brand_id
    JOIN vehicle_classes c ON c.class_id = v.class_id
    JOIN engine_types et   ON et.engine_type_id = v.engine_type_id
    JOIN transmissions t   ON t.transmission_id = v.transmission_id
    JOIN fuel_types f      ON f.fuel_type_id = v.fuel_type_id
    WHERE 1=1
    """

    params: Dict[str, Any] = {"limit": int(limit)}

    # Salary/purpose category filter -> class ids
    if class_ids:
        sql += " AND v.class_id = ANY(%(class_ids)s)"
        params["class_ids"] = list(map(int, class_ids))

    # Fuel preference (optional)
    if fuel_type_id is not None:
        sql += " AND v.fuel_type_id = %(fuel_type_id)s"
        params["fuel_type_id"] = int(fuel_type_id)

    # Transmission preference (optional)
    if transmission_ids:
        sql += " AND v.transmission_id = ANY(%(transmission_ids)s)"
        params["transmission_ids"] = list(map(int, transmission_ids))

    # Max combined L/100km (optional)
    if max_comb is not None:
        sql += " AND v.fuel_efficiency_combined <= %(max_comb)s"
        params["max_comb"] = float(max_comb)

    sql += " ORDER BY v.vehicle_id DESC LIMIT %(limit)s;"

    with psycopg2.connect(**db) as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    return df


# =========================
# 7) Convert DB rows -> ML schema (same as your CSV expects)
# =========================
def convert_candidates_to_ml_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["Engine Type"] = out["ENGINE_TYPE_NAME"].astype(str).str.upper().str[0]
    out["CYLINDERS"] = out["ENGINE_TYPE_NAME"].apply(parse_cylinders)
    out["TRANSMISSION"] = out["TRANSMISSION_NAME"].apply(trans_category)
    out["FUEL"] = out["FUEL_TYPE_NAME"].apply(lambda x: first_letter(str(x)) if pd.notna(x) else None)
    out["COMB (mpg)"] = out["COMB (L/100 km)"].apply(l_per_100_to_mpg)
    out["FUEL CONSUMPTION HWY (L/100 km)"] = out["HWY (L/100 km)"]
    out["EMISSIONS"] = pd.to_numeric(out["COMB (L/100 km)"], errors="coerce") * 20.0

    numeric_cols = [
        "YEAR",
        "ENGINE SIZE",
        "CYLINDERS",
        "COMB (L/100 km)",
        "COMB (mpg)",
        "HWY (L/100 km)",
        "FUEL CONSUMPTION HWY (L/100 km)",
        "EMISSIONS",
    ]
    for c in numeric_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    if out["CYLINDERS"].notna().any():
        out["CYLINDERS"] = out["CYLINDERS"].fillna(out["CYLINDERS"].median())
    else:
        out["CYLINDERS"] = out["CYLINDERS"].fillna(4)

    if out["ENGINE SIZE"].notna().any():
        out["ENGINE SIZE"] = out["ENGINE SIZE"].fillna(out["ENGINE SIZE"].median())

    if out["COMB (L/100 km)"].notna().any():
        out["COMB (L/100 km)"] = out["COMB (L/100 km)"].fillna(out["COMB (L/100 km)"].median())

    return out


# =========================
# 8) PATCH: Disable year filtering in your ML class
#    (we do NOT want manufacturing year filtering at all)
# =========================
def patch_disable_year_filter(ml: VehicleRecommender) -> None:
    """
    Monkey-patch ml._apply_filters to ignore ALL year filtering, including salary proxy.
    Keeps only max_fuel_consumption and (optional) family class preference.
    """
    def _apply_filters_no_year(user_profile: Dict) -> pd.DataFrame:
        original = ml.original_data.copy()

        # ✅ NO salary->year filtering
        # ✅ NO year_min/year_max filtering

        # Fuel consumption filter (still useful)
        if "max_fuel_consumption" in user_profile:
            max_fuel = float(user_profile["max_fuel_consumption"])
            original = original[original["COMB (L/100 km)"] <= max_fuel]

        # Vehicle class preferences based on primary need (as in your original code)
        need = user_profile.get("primary_need", "economy")
        if need == "family":
            preferred_classes = ["MID-SIZE", "SUV - SMALL", "SUV - STANDARD", "MINIVAN"]
            mask = original["VEHICLE CLASS"].astype(str).str.upper().isin(preferred_classes)
            if mask.sum() > 0:
                original = original[mask]

        return ml.vehicle_data.loc[original.index]

    ml._apply_filters = _apply_filters_no_year  # type: ignore


# =========================
# 9) Pipeline Wrapper (Logical -> DB -> ML)
# =========================
class DBPipelineRecommender:
    def __init__(self, db_config: Dict[str, Any]):
        self.db = db_config
        self.cache = load_lookup_cache(db_config)
        self.ml = VehicleRecommender()  # loads pkl models/encoders/etc.
        patch_disable_year_filter(self.ml)  # ✅ IMPORTANT

    def recommend(
        self,
        user_input: Dict[str, Any],
        top_n: int = 10,
        candidate_limit: int = 3000,
    ) -> pd.DataFrame:
        """
        Full pipeline:
          user_input -> SQL candidate filtering -> ML scoring -> top_n output
        """
        candidates = fetch_candidates_from_db(self.db, self.cache, user_input, limit=candidate_limit)

        if candidates.empty:
            return pd.DataFrame(
                {"message": ["No vehicles matched your DB hard filters. Try relaxing fuel/transmission/max_comb."]}
            )

        ml_df = convert_candidates_to_ml_schema(candidates)

        self.ml.original_data = ml_df.copy()
        self.ml.vehicle_data = self.ml._prepare_vehicle_data(ml_df.copy())

        # ML profile (still NO year filtering)
        model_profile = {
            "primary_need": purpose_to_primary_need(user_input.get("purpose", "daily_commute")),
            "usage": area_to_usage(user_input.get("area", "mixed")),
        }
        if user_input.get("max_comb_l_per_100") is not None:
            model_profile["max_fuel_consumption"] = float(user_input["max_comb_l_per_100"])

        results = self.ml.get_recommendations(model_profile, top_n=top_n)

        merged = results.merge(
            candidates[["vehicle_id", "YEAR", "MAKE", "MODEL", "VEHICLE CLASS"]],
            on=["YEAR", "MAKE", "MODEL", "VEHICLE CLASS"],
            how="left",
        )

        return merged


# =========================
# 10) Example usage
# =========================
if __name__ == "__main__":
    # ✅ Now you can pass monthly income OR salary_level
    # monthly_income will automatically map to:
    # <150k low, 150k-600k medium, 600k-999,999 high, >=1,000,000 luxury
    user_input = {
        "monthly_income": 1000000,        # <-- NEW (try 200000, 700000, 1200000)
        # "salary_level": "medium",      # <-- optional override
        "purpose": "luxury",
        "area": "Highway",
        "fuel": "Z - premium Gasoline",
        "transmission": "A=Automatic",
        "max_comb_l_per_100": 15,
    }

    pipeline = DBPipelineRecommender(DB_CONFIG)
    top = pipeline.recommend(user_input, top_n=10, candidate_limit=2000)

    print("\n🏆 TOP RECOMMENDATIONS\n")
    print(top.to_string(index=False))
