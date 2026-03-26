from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import psycopg2

from vehicle_recommender import VehicleRecommender


# =========================
# DB CONFIG
# =========================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "autofyx-autofyx.l.aivencloud.com"),
    "port": int(os.getenv("DB_PORT", "17459")),
    "database": os.getenv("DB_NAME", "autofyx"),
    "user": os.getenv("DB_USER", "avnadmin"),
    "password": os.getenv("DB_PASSWORD", "AVNS_2AEJXab9YDAGyXW6vas"),
}


# =========================
# Helpers
# =========================

def first_letter(text):
    if text is None:
        return None
    return str(text).strip().upper()[0]


def l_per_100_to_mpg(l):
    if l is None or l <= 0:
        return None
    return 235.214583 / l


def parse_cylinders(engine_type):
    """
    Convert engine type like I4, V6 → cylinders
    """
    if not engine_type:
        return None

    match = re.search(r"(\d+)", str(engine_type))
    if match:
        return int(match.group(1))

    return None


def trans_category(trans):
    """
    Convert transmission types to ML format
    """

    if not trans:
        return "Unknown"

    t = str(trans).upper()

    if t.startswith("AM"):
        return "AM"
    if t.startswith("AS"):
        return "AS"
    if t.startswith("AV"):
        return "AV"
    if t.startswith("A"):
        return "A"
    if t.startswith("M"):
        return "MANUAL"

    return "Unknown"


# =========================
# Fetch vehicles from DB
# =========================

def fetch_candidates_from_db(db_config, limit=3000):

    query = """
    SELECT
        v.vehicle_id,
        v.manufacturing_year AS "YEAR",
        b.brand_name AS "Make",
        v.model_name AS "Model",
        c.class_name AS "VEHICLE CLASS",
        v.engine_size AS "ENGINE SIZE",
        et.engine_type_name AS "ENGINE TYPE",
        t.transmission_name AS "Transmission",
        f.fuel_type_name AS "FUEL",
        v.fuel_efficiency_combined AS "COMB (L/100 km)",
        v.fuel_efficiency_highway AS "HWY (L/100 km)"
    FROM vehicles v
    JOIN brands b ON b.brand_id = v.brand_id
    JOIN vehicle_classes c ON c.class_id = v.class_id
    JOIN engine_types et ON et.engine_type_id = v.engine_type_id
    JOIN transmissions t ON t.transmission_id = v.transmission_id
    JOIN fuel_types f ON f.fuel_type_id = v.fuel_type_id
    ORDER BY v.vehicle_id DESC
    LIMIT %s
    """

    conn = psycopg2.connect(**db_config)

    df = pd.read_sql_query(query, conn, params=(limit,))

    conn.close()

    return df


# =========================
# Convert DB schema → ML schema
# =========================

def convert_candidates_to_ml_schema(df):

    out = df.copy()

    # ENGINE TYPE → I,V,W
    out["ENGINE TYPE"] = out["ENGINE TYPE"].astype(str).str[0]

    # Cylinders
    out["CYLINDERS"] = df["ENGINE TYPE"].apply(parse_cylinders)

    # Transmission
    out["Transmission"] = df["Transmission"].apply(trans_category)

    # Fuel
    out["FUEL"] = df["FUEL"].apply(first_letter)

    # MPG
    out["COMB (mpg)"] = df["COMB (L/100 km)"].apply(l_per_100_to_mpg)

    # Emissions estimation
    out["EMISSIONS"] = df["COMB (L/100 km)"] * 20

    numeric_cols = [
        "YEAR",
        "ENGINE SIZE",
        "CYLINDERS",
        "COMB (L/100 km)",
        "COMB (mpg)",
        "HWY (L/100 km)",
        "EMISSIONS",
    ]

    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # fill missing values
    out["CYLINDERS"] = out["CYLINDERS"].fillna(4)
    out["ENGINE SIZE"] = out["ENGINE SIZE"].fillna(out["ENGINE SIZE"].median())

    # Add HORSEPOWER estimate (same logic as load_vehicle_inventory)
    out["HORSEPOWER"] = out["ENGINE SIZE"] * out["CYLINDERS"] * 20

    # Add MAINTENANCE COST estimate (same logic as load_vehicle_inventory)
    base_cost = 50000
    out["MAINTENANCE COST"] = (
        base_cost +
        out["ENGINE SIZE"] * 30000 +
        out["CYLINDERS"] * 15000 +
        (2024 - out["YEAR"]) * 5000
    )

    return out



# =========================
# Main Pipeline
# =========================

class DBPipelineRecommender:

    def __init__(self, db_config):

        self.db = db_config

        # ML recommender
        self.ml = VehicleRecommender()

    def recommend(self, user_profile, top_n=10, candidate_limit=2000):

        print("\nLoading vehicles from database...")

        candidates = fetch_candidates_from_db(self.db, limit=candidate_limit)

        if candidates.empty:
            print("No vehicles found in DB")
            return pd.DataFrame([{"message": "No vehicles found in the database."}])

        # convert schema
        ml_df = convert_candidates_to_ml_schema(candidates)

        # load data into ML model
        self.ml.original_data = ml_df.copy()
        self.ml.vehicle_data = self.ml._prepare_vehicle_data(ml_df.copy())

        # get recommendations
        results = self.ml.get_recommendations(user_profile, top_n=top_n)

        return results


# =========================
# Example usage
# =========================

if __name__ == "__main__":

    pipeline = DBPipelineRecommender(DB_CONFIG)

    user_profile = {
        "salary_level": "medium",
        "primary_need": "economy",
        "usage": "highway",
        "max_fuel_consumption": 15
    }

    recommendations = pipeline.recommend(user_profile, top_n=10)

    print("\n🏆 TOP RECOMMENDATIONS\n")
    print(recommendations.to_string(index=False))
