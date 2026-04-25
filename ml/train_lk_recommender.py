"""
train_lk_recommender.py
=======================
Sri Lanka–aware retraining script.

What this script does
---------------------
1. Loads dataset/vehicledata.csv (the same data used for the original 7-target models).
2. Engineers all proxy features that the existing pipeline expects
   (brand_reliability_score, MAINTENANCE_COST_PROXY, engine_* scores, etc.)
3. Builds a new proxy label:  `maintainability_score`
   - Combines brand origin, fuel efficiency, engine simplicity, and vehicle age.
4. Trains a RandomForestRegressor pipeline (same architecture as existing models)
   for `maintainability_score`.
5. Patches the new model into ml/vehicle_ranking_models_past.pkl WITHOUT touching
   the existing 7 target models.
6. Updates ml/vehicle_training_metadata_past.pkl to record the new target.

Run from the project root:
    python ml/train_lk_recommender.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── Make sure project root is importable ──────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent          # api/ml/
API_ROOT   = SCRIPT_DIR.parent                        # api/
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ── Paths ─────────────────────────────────────────────────────────────────────
DATASET_PATH   = API_ROOT / "dataset" / "vehicledata.csv"
MODELS_PATH    = SCRIPT_DIR / "vehicle_ranking_models_past.pkl"
METADATA_PATH  = SCRIPT_DIR / "vehicle_training_metadata_past.pkl"

# ── Sri Lanka brand tables ────────────────────────────────────────────────────

JAPANESE_BRANDS = {
    "TOYOTA", "HONDA", "NISSAN", "MAZDA", "MITSUBISHI",
    "SUBARU", "SUZUKI", "DAIHATSU", "ISUZU",
}
KOREAN_BRANDS   = {"KIA", "HYUNDAI"}
EUROPEAN_BRANDS = {
    "BMW", "MERCEDES-BENZ", "AUDI", "VOLKSWAGEN", "VOLVO",
    "PEUGEOT", "RENAULT", "LAND ROVER", "JAGUAR", "MINI",
}
AMERICAN_BRANDS = {"FORD", "CHEVROLET", "DODGE", "JEEP", "BUICK", "CADILLAC"}


def _brand_origin_score(make: str) -> float:
    """
    Return a [0,1] maintainability-affinity score for a brand.
    Reflects parts availability and repair cost in Sri Lanka.
    """
    m = str(make).strip().upper()
    if m in JAPANESE_BRANDS: return 1.00
    if m in KOREAN_BRANDS:   return 0.85
    if m in AMERICAN_BRANDS: return 0.45
    if m in EUROPEAN_BRANDS: return 0.30
    return 0.50   # unknown / other


# ── Vehicle-class space score (rule-based, no training) ───────────────────────

# Vehicle class → space/cabin score [0,1]
# Keys MUST match exact DB / CSV values (spaces around hyphens).
CLASS_SPACE_SCORE: dict[str, float] = {
    "KEI CAR":        0.25,  # micro hatchback — very cramped
    "MINICOMPACT":    0.32,  # slightly more room
    "SUBCOMPACT":     0.50,  # hatchback/small sedan — adequate
    "COMPACT":        0.65,  # workhorse sedan
    "WAGON":          0.75,  # extended cargo + passenger
    "MID - SIZE":     0.82,  # DB exact
    "MPV":            0.92,  # van / people mover — very spacious
    "SUV - SMALL":    0.80,  # DB exact
    "SUV - STANDARD": 0.90,  # DB exact
    "SUV":            0.88,  # generic SUV
    "FULL - SIZE":    0.95,  # DB exact
    "OFF - ROAD":     0.85,  # DB exact — large body but utility focus
}


def _class_space_score(vehicle_class: str) -> float:
    key = str(vehicle_class).strip().upper()
    return CLASS_SPACE_SCORE.get(key, 0.60)


# ── Brand scores already expected by existing pipeline ────────────────────────
# (Kept consistent with whatever the original training used so feature ordering
#  of existing models is untouched.)

# ── Brand scores ─────────────────────────────────────────────────────────────
# Scores reflect Sri Lankan market realities: Japanese brands score highest
# for reliability and maintenance due to parts availability and service network.
BRAND_RELIABILITY: dict[str, float] = {
    "TOYOTA": 0.98, "HONDA": 0.95, "MAZDA": 0.93, "SUZUKI": 0.92,
    "DAIHATSU": 0.90, "SUBARU": 0.88, "NISSAN": 0.86, "MITSUBISHI": 0.84,
    "ISUZU": 0.85, "HYUNDAI": 0.80, "KIA": 0.78,
    "VOLKSWAGEN": 0.70, "FORD": 0.72, "CHEVROLET": 0.70,
    "VOLVO": 0.68, "AUDI": 0.65, "MERCEDES-BENZ": 0.62, "BMW": 0.60,
    "LAND ROVER": 0.50,
}
BRAND_MAINTENANCE: dict[str, float] = {
    "TOYOTA": 0.96, "SUZUKI": 0.94, "DAIHATSU": 0.93, "HONDA": 0.92,
    "MAZDA": 0.90, "ISUZU": 0.88, "NISSAN": 0.85, "MITSUBISHI": 0.83,
    "SUBARU": 0.80, "HYUNDAI": 0.78, "KIA": 0.76,
    "FORD": 0.70, "CHEVROLET": 0.68, "VOLKSWAGEN": 0.65,
    "VOLVO": 0.60, "AUDI": 0.55, "MERCEDES-BENZ": 0.48, "BMW": 0.45,
    "LAND ROVER": 0.40,
}
BRAND_PERFORMANCE: dict[str, float] = {
    "BMW": 0.95, "AUDI": 0.92, "MERCEDES-BENZ": 0.90, "VOLKSWAGEN": 0.82,
    "SUBARU": 0.80, "HONDA": 0.78, "MITSUBISHI": 0.76, "MAZDA": 0.74,
    "NISSAN": 0.72, "FORD": 0.75, "CHEVROLET": 0.73, "TOYOTA": 0.70,
    "VOLVO": 0.70, "LAND ROVER": 0.72, "HYUNDAI": 0.65, "KIA": 0.63,
}
BRAND_OFFROAD: dict[str, float] = {
    "LAND ROVER": 0.98, "MITSUBISHI": 0.88, "TOYOTA": 0.85, "SUBARU": 0.83,
    "NISSAN": 0.76, "ISUZU": 0.80, "FORD": 0.72, "CHEVROLET": 0.70,
    "MERCEDES-BENZ": 0.62, "HONDA": 0.60, "BMW": 0.55, "KIA": 0.55,
    "HYUNDAI": 0.52, "MAZDA": 0.55, "AUDI": 0.50, "VOLKSWAGEN": 0.50,
}

# ── Class score maps — MUST use exact DB/CSV class names ──────────────────────
# DB class names have spaces around hyphens: "MID - SIZE", "FULL - SIZE",
# "SUV - SMALL", "SUV - STANDARD", "OFF - ROAD"
CLASS_OFFROAD: dict[str, float] = {
    "OFF - ROAD":    1.00,   # DB exact
    "SUV - STANDARD":0.80,   # DB exact
    "SUV":           0.75,
    "SUV - SMALL":   0.55,   # DB exact
    "MPV":           0.40,
    "WAGON":         0.30,
    "MID - SIZE":    0.20,   # DB exact
    "COMPACT":       0.15,
    "SUBCOMPACT":    0.10,
    "MINICOMPACT":   0.05,
    "KEI CAR":       0.05,
    "FULL - SIZE":   0.20,   # DB exact
}
CLASS_CITY: dict[str, float] = {
    "KEI CAR":        1.00,  # best city car
    "MINICOMPACT":    0.95,
    "SUBCOMPACT":     0.88,
    "COMPACT":        0.80,
    "WAGON":          0.60,
    "MID - SIZE":     0.60,  # DB exact
    "MPV":            0.50,
    "SUV - SMALL":    0.48,  # DB exact
    "SUV - STANDARD": 0.35,  # DB exact
    "SUV":            0.35,
    "FULL - SIZE":    0.25,  # DB exact
    "OFF - ROAD":     0.20,  # DB exact
}
CLASS_FAMILY: dict[str, float] = {
    "MPV":            1.00,  # best family vehicle in LK (Voxy, Noah, Alphard)
    "SUV - STANDARD": 0.92,  # DB exact
    "SUV":            0.88,
    "WAGON":          0.85,
    "SUV - SMALL":    0.78,  # DB exact
    "MID - SIZE":     0.80,  # DB exact
    "FULL - SIZE":    0.72,  # DB exact
    "COMPACT":        0.52,
    "SUBCOMPACT":     0.35,
    "MINICOMPACT":    0.20,
    "KEI CAR":        0.15,
    "OFF - ROAD":     0.60,  # DB exact
}
CLASS_LUXURY: dict[str, float] = {
    "FULL - SIZE":    0.92,  # DB exact
    "MID - SIZE":     0.78,  # DB exact
    "SUV - STANDARD": 0.72,  # DB exact
    "SUV":            0.70,
    "MPV":            0.65,  # Alphard = ultra luxury in LK
    "WAGON":          0.55,
    "SUV - SMALL":    0.52,  # DB exact
    "COMPACT":        0.40,
    "SUBCOMPACT":     0.25,
    "MINICOMPACT":    0.15,
    "KEI CAR":        0.05,
    "OFF - ROAD":     0.38,  # DB exact
}
CLASS_HIGHWAY: dict[str, float] = {
    "FULL - SIZE":    0.92,  # DB exact
    "MID - SIZE":     0.82,  # DB exact
    "WAGON":          0.76,
    "SUV - STANDARD": 0.72,  # DB exact
    "SUV":            0.70,
    "MPV":            0.60,
    "SUV - SMALL":    0.58,  # DB exact
    "COMPACT":        0.55,
    "SUBCOMPACT":     0.45,
    "MINICOMPACT":    0.35,
    "KEI CAR":        0.25,
    "OFF - ROAD":     0.52,  # DB exact
}

ENGINE_POWER: dict[str, float]     = {"I": 0.70, "V": 0.90, "V or I": 0.80}
ENGINE_RUGGED: dict[str, float]    = {"I": 0.80, "V": 0.70, "V or I": 0.75}
ENGINE_EFFIC: dict[str, float]     = {"I": 0.85, "V": 0.60, "V or I": 0.72}
ENGINE_MAINT: dict[str, float]     = {"I": 0.90, "V": 0.65, "V or I": 0.77}

# Transmission type → score maps (prefix-based)
def _trans_score(trans: str, mapping: dict) -> float:
    t = str(trans).strip().upper()
    for prefix, val in mapping.items():
        if t.startswith(prefix):
            return val
    return 0.50

TRANS_PERFORMANCE = {"A": 0.75, "AM": 0.85, "AS": 0.80, "M": 0.70, "AV": 0.65}
TRANS_RUGGED      = {"A": 0.60, "AM": 0.70, "AS": 0.65, "M": 0.85, "AV": 0.55}
TRANS_EFFIC       = {"A": 0.70, "AM": 0.80, "AS": 0.78, "M": 0.75, "AV": 0.85}
TRANS_MAINT       = {"A": 0.65, "AM": 0.60, "AS": 0.62, "M": 0.90, "AV": 0.70}


# ── Main feature engineering ──────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduce ALL proxy features expected by the existing model pipeline,
    PLUS the new `lk_brand_origin_score` and `space_score`.
    """
    df = df.copy()

    # Normalise column names to match existing pipeline expectations
    rename = {
        "MAKE": "Make", "MODEL": "Model",
        "TRANSMISSION": "Transmission",
        "Engine Type": "ENGINE TYPE",
        "FUEL CONSUMPTION": "CITY (L/100 km)",
    }
    df.rename(columns=rename, inplace=True)

    # ── Numeric coercions ──────────────────────────────────────────────────
    numeric_cols = [
        "YEAR", "ENGINE SIZE", "CYLINDERS",
        "CITY (L/100 km)", "HWY (L/100 km)", "COMB (L/100 km)",
        "COMB (mpg)", "EMISSIONS",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Normalise categorical fields ───────────────────────────────────────
    df["Make"]          = df["Make"].astype(str).str.strip().str.upper()
    df["Model"]         = df["Model"].astype(str).str.strip().str.upper()
    df["VEHICLE CLASS"] = df["VEHICLE CLASS"].astype(str).str.strip().str.upper()
    df["Transmission"]  = df["Transmission"].astype(str).str.strip().str.upper()
    df["ENGINE TYPE"]   = df["ENGINE TYPE"].astype(str).str.strip().str.upper()
    df["FUEL"]          = df["FUEL"].astype(str).str.strip().str.upper()

    current_year = 2025

    # ── Proxy features matching existing model feature_columns ────────────
    df["HORSEPOWER_PROXY"]      = df["ENGINE SIZE"] * df["CYLINDERS"] * 15
    df["VEHICLE_AGE"]           = current_year - df["YEAR"]
    df["MAINTENANCE_COST_PROXY"] = (
        df["VEHICLE_AGE"] * 0.3
        + df["ENGINE SIZE"] * 0.4
        + df["CYLINDERS"] * 0.1
    )

    df["engine_power_score"]       = df["ENGINE TYPE"].map(ENGINE_POWER).fillna(0.75)
    df["engine_ruggedness_score"]  = df["ENGINE TYPE"].map(ENGINE_RUGGED).fillna(0.75)
    df["engine_efficiency_score"]  = df["ENGINE TYPE"].map(ENGINE_EFFIC).fillna(0.75)
    df["engine_maintenance_score"] = df["ENGINE TYPE"].map(ENGINE_MAINT).fillna(0.75)

    df["trans_performance_score"] = df["Transmission"].apply(lambda t: _trans_score(t, TRANS_PERFORMANCE))
    df["trans_ruggedness_score"]  = df["Transmission"].apply(lambda t: _trans_score(t, TRANS_RUGGED))
    df["trans_efficiency_score"]  = df["Transmission"].apply(lambda t: _trans_score(t, TRANS_EFFIC))
    df["trans_maintenance_score"] = df["Transmission"].apply(lambda t: _trans_score(t, TRANS_MAINT))

    df["driving_pleasure_score"]  = (
        df["engine_power_score"] * 0.5 + df["trans_performance_score"] * 0.5
    )

    df["brand_reliability_score"]  = df["Make"].map(BRAND_RELIABILITY).fillna(0.65)
    df["brand_maintenance_score"]  = df["Make"].map(BRAND_MAINTENANCE).fillna(0.65)
    df["brand_performance_score"]  = df["Make"].map(BRAND_PERFORMANCE).fillna(0.65)
    df["brand_offroad_score"]      = df["Make"].map(BRAND_OFFROAD).fillna(0.50)

    df["class_offroad_score"]  = df["VEHICLE CLASS"].map(CLASS_OFFROAD).fillna(0.30)
    df["class_city_score"]     = df["VEHICLE CLASS"].map(CLASS_CITY).fillna(0.50)
    df["class_family_score"]   = df["VEHICLE CLASS"].map(CLASS_FAMILY).fillna(0.50)
    df["class_luxury_score"]   = df["VEHICLE CLASS"].map(CLASS_LUXURY).fillna(0.40)
    df["class_highway_score"]  = df["VEHICLE CLASS"].map(CLASS_HIGHWAY).fillna(0.55)

    comb_min = df["COMB (L/100 km)"].min()
    comb_max = df["COMB (L/100 km)"].max()
    comb_range = comb_max - comb_min if comb_max != comb_min else 1.0

    df["fuel_efficiency_score"]    = 1.0 - (df["COMB (L/100 km)"] - comb_min) / comb_range
    df["city_efficiency_score"]    = 1.0 - (df["CITY (L/100 km)"] - df["CITY (L/100 km)"].min()) / (
        (df["CITY (L/100 km)"].max() - df["CITY (L/100 km)"].min()) or 1.0
    )
    df["highway_efficiency_score"] = 1.0 - (df["HWY (L/100 km)"] - df["HWY (L/100 km)"].min()) / (
        (df["HWY (L/100 km)"].max() - df["HWY (L/100 km)"].min()) or 1.0
    )

    emit_max = df["EMISSIONS"].max()
    df["emission_score"]     = 1.0 - df["EMISSIONS"] / (emit_max or 1.0)
    df["power_to_size_ratio"]= df["HORSEPOWER_PROXY"] / (df["ENGINE SIZE"] + 0.01)
    df["power_per_cylinder"] = df["HORSEPOWER_PROXY"] / (df["CYLINDERS"] + 0.01)
    df["emissions_per_power"]= df["EMISSIONS"] / (df["HORSEPOWER_PROXY"] + 0.01)
    df["city_vs_highway_gap"]= df["CITY (L/100 km)"] - df["HWY (L/100 km)"]
    df["estimated_price_category"] = pd.cut(
        df["VEHICLE_AGE"],
        bins=[-1, 3, 7, 12, 20, 9999],
        labels=[4, 3, 2, 1, 0],
    ).astype(float)

    # ── NEW: Sri Lanka–specific features ─────────────────────────────────
    df["lk_brand_origin_score"] = df["Make"].apply(_brand_origin_score)
    df["lk_space_score"]        = df["VEHICLE CLASS"].apply(_class_space_score)

    return df


# ── Proxy label builders ───────────────────────────────────────────────────────

def build_maintainability_label(df: pd.DataFrame) -> pd.Series:
    """
    Composite maintainability_score ∈ [0, 1].

    Component                   Weight  Rationale
    ─────────────────────────   ──────  ─────────────────────────────────────
    lk_brand_origin_score        0.35   Parts availability & brand trust in LK
    fuel_efficiency_score        0.25   Cheaper running = effectively lower TCO
    engine_maintenance_score     0.20   Simpler engine type = less failure
    trans_maintenance_score      0.10   Manual > Auto for rural maintenance
    age_penalty (inverted)       0.10   Newer = better parts, fewer surprises
    """
    age_max = df["VEHICLE_AGE"].max() or 1.0
    age_score = 1.0 - (df["VEHICLE_AGE"] / age_max)

    raw = (
        df["lk_brand_origin_score"]   * 0.35
        + df["fuel_efficiency_score"] * 0.25
        + df["engine_maintenance_score"] * 0.20
        + df["trans_maintenance_score"]  * 0.10
        + age_score                      * 0.10
    )
    # Normalise to [0, 1]
    return (raw - raw.min()) / (raw.max() - raw.min() + 1e-9)


def build_existing_target_labels(df: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Reconstruct the 7 existing proxy labels so we can see their distributions
    and optionally retrain them if needed in the future. Not used in patching.
    """
    return {
        "economy_score": (
            df["fuel_efficiency_score"] * 0.50
            + df["city_efficiency_score"] * 0.25
            + df["brand_maintenance_score"] * 0.25
        ),
        "performance_score": (
            df["engine_power_score"] * 0.40
            + df["trans_performance_score"] * 0.30
            + df["brand_performance_score"] * 0.30
        ),
        "luxury_score": (
            df["class_luxury_score"] * 0.50
            + df["brand_performance_score"] * 0.30
            + df["estimated_price_category"].fillna(0) / 4.0 * 0.20
        ),
        "family_score": (
            df["class_family_score"] * 0.55
            + df["brand_reliability_score"] * 0.25
            + df["fuel_efficiency_score"] * 0.20
        ),
        "city_score": (
            df["class_city_score"] * 0.55
            + df["city_efficiency_score"] * 0.30
            + df["emission_score"] * 0.15
        ),
        "highway_score": (
            df["class_highway_score"] * 0.50
            + df["highway_efficiency_score"] * 0.35
            + df["engine_power_score"] * 0.15
        ),
        "offroad_score": (
            df["class_offroad_score"] * 0.60
            + df["brand_offroad_score"] * 0.25
            + df["engine_ruggedness_score"] * 0.15
        ),
    }


# ── Pipeline builder ───────────────────────────────────────────────────────────

def build_rf_pipeline(feature_columns: list[str]) -> Pipeline:
    """
    Mirror the exact sklearn Pipeline architecture used by the existing models:
      ColumnTransformer(numeric median-imputer | categorical OHE) → RandomForest
    """
    metadata = joblib.load(METADATA_PATH)
    numeric_features     = [f for f in metadata["numeric_features"] if f in feature_columns]
    categorical_features = [f for f in metadata["categorical_features"] if f in feature_columns]

    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer([
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features),
    ])
    model = RandomForestRegressor(
        n_estimators=350,
        max_depth=24,
        min_samples_split=4,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


# ── Training entry point ───────────────────────────────────────────────────────

def train_and_patch():
    print("=" * 60)
    print(" Sri Lanka Recommender — Maintainability Model Training")
    print("=" * 60)

    # 1. Load dataset
    print(f"\n[1/6] Loading dataset from: {DATASET_PATH}")
    raw_df = pd.read_csv(DATASET_PATH).drop_duplicates().reset_index(drop=True)
    print(f"      Rows: {len(raw_df):,}  |  Columns: {list(raw_df.columns)}")

    # 2. Feature engineering
    print("\n[2/6] Engineering features …")
    df = engineer_features(raw_df)
    print(f"      Features available: {df.shape[1]} columns")

    # 3. Build maintainability label
    print("\n[3/6] Building maintainability_score proxy label …")
    y_maintain = build_maintainability_label(df)
    print(f"      Label stats → min={y_maintain.min():.3f}  "
          f"mean={y_maintain.mean():.3f}  max={y_maintain.max():.3f}")

    # 4. Prepare feature matrix (use existing feature column list)
    print("\n[4/6] Loading existing model metadata for feature alignment …")
    metadata = joblib.load(METADATA_PATH)
    all_feature_columns: list[str] = list(metadata["all_feature_columns"])

    # Add new LK features if not already present
    for new_feat in ["lk_brand_origin_score", "lk_space_score"]:
        if new_feat not in all_feature_columns:
            all_feature_columns.append(new_feat)

    # Ensure all required columns exist (fill zeros for any missing)
    for feat in all_feature_columns:
        if feat not in df.columns:
            print(f"      ⚠  Feature '{feat}' not found in engineered data — filling 0")
            df[feat] = 0.0

    X = df[all_feature_columns].copy()
    print(f"      Feature matrix: {X.shape}")

    # 5. Train maintainability_score pipeline
    print("\n[5/6] Training RandomForest for maintainability_score …")
    pipe = build_rf_pipeline(all_feature_columns)
    pipe.fit(X, y_maintain)

    preds = pipe.predict(X)
    residuals = y_maintain.values - preds
    rmse = float(np.sqrt((residuals ** 2).mean()))
    print(f"      Training RMSE: {rmse:.4f}  (in-sample, for sanity check only)")

    # Quick feature importance (top 10)
    rf_model = pipe.named_steps["model"]
    preprocessor = pipe.named_steps["preprocessor"]
    try:
        ohe = preprocessor.named_transformers_["cat"].named_steps["onehot"]
        cat_names = list(ohe.get_feature_names_out(
            [f for f in metadata["categorical_features"] if f in all_feature_columns]
        ))
        num_names = [f for f in metadata["numeric_features"] if f in all_feature_columns]
        feature_names = num_names + cat_names
        importances = rf_model.feature_importances_
        top_idx = np.argsort(importances)[::-1][:10]
        print("\n      Top-10 feature importances:")
        for i in top_idx:
            if i < len(feature_names):
                print(f"        {feature_names[i]:<40s} {importances[i]:.4f}")
    except Exception:
        pass  # Non-critical

    # 6. Patch into existing pkl
    print("\n[6/6] Patching vehicle_ranking_models_past.pkl …")
    models = joblib.load(MODELS_PATH)
    models["maintainability_score"] = pipe
    joblib.dump(models, MODELS_PATH, compress=3)
    print(f"      Saved {len(models)} models: {sorted(models.keys())}")

    # Update metadata
    metadata["all_feature_columns"] = all_feature_columns
    if "maintainability_score" not in metadata["targets"]:
        metadata["targets"].append("maintainability_score")
    # Track new LK features
    for new_feat in ["lk_brand_origin_score", "lk_space_score"]:
        if new_feat not in metadata.get("numeric_features", []):
            metadata.setdefault("numeric_features", []).append(new_feat)
    joblib.dump(metadata, METADATA_PATH)
    print(f"      Updated metadata targets: {metadata['targets']}")

    print("\n✅  Training complete!")
    print(f"    Models saved to : {MODELS_PATH}")
    print(f"    Metadata saved  : {METADATA_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    train_and_patch()
