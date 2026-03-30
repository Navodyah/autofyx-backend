
import re
import joblib
import pandas as pd


def _norm_text(value):
    text = "" if value is None else str(value)
    text = text.strip().upper().replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text if text else "UNKNOWN"


def normalize_make(value):
    return _norm_text(value)


def normalize_model(value):
    return _norm_text(value)


def normalize_vehicle_class(value):
    return _norm_text(value)


def normalize_transmission(value):
    text = _norm_text(value)
    if text in {"A", "AT", "AUTOMATIC"}:
        return "AUTO"
    if text in {"M", "MT", "MANUAL"}:
        return "MANUAL"
    return text


def normalize_engine_type(value):
    return _norm_text(value)


def normalize_fuel(value):
    text = _norm_text(value)
    mapping = {
        "X": "REGULAR",
        "Z": "PREMIUM",
        "D": "DIESEL",
        "E": "ELECTRIC",
    }
    return mapping.get(text, text)


def add_proxy_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "COMB (L/100 km)" in out.columns:
        out["fuel_efficiency_inverse"] = 1.0 / out["COMB (L/100 km)"].replace(0, pd.NA)
        out["fuel_efficiency_inverse"] = out["fuel_efficiency_inverse"].fillna(0.0)

    if "ENGINE SIZE" in out.columns and "CYLINDERS" in out.columns:
        out["engine_per_cylinder"] = (
            out["ENGINE SIZE"] / out["CYLINDERS"].replace(0, pd.NA)
        ).fillna(0.0)

    return out

MODEL_PATH = "trained_vehicle_system/vehicle_ranking_models.pkl"
METADATA_PATH = "trained_vehicle_system/vehicle_training_metadata.pkl"
DATASET_PATH = "vehicledata.csv"

TARGET_KEYWORDS = {
    "economy_score": [
        "economy", "fuel", "cheap", "save", "budget", "efficient", "mileage"
    ],
    "performance_score": [
        "performance", "fast", "speed", "power", "sport", "acceleration"
    ],
    "luxury_score": [
        "luxury", "premium", "comfort", "high-end", "executive"
    ],
    "family_score": [
        "family", "kids", "spacious", "safe", "reliable"
    ],
    "city_score": [
        "city", "urban", "traffic", "parking", "daily commute", "compact"
    ],
    "highway_score": [
        "highway", "long drive", "touring", "distance", "road trip"
    ],
    "offroad_score": [
        "offroad", "4x4", "trail", "adventure", "rugged", "mountain"
    ],
}

SALARY_YEAR_MAP = {
    "low": (2000, 2015),
    "medium": (2010, 2020),
    "high": (2015, 2024),
    "luxury": (2018, 2024),
}

PRIMARY_NEED_CLASS_MAP = {
    "family": ["MID-SIZE", "SUV - SMALL", "SUV - STANDARD", "MINIVAN"],
}

def load_models():
    models = joblib.load(MODEL_PATH)
    metadata = joblib.load(METADATA_PATH)
    return models, metadata

def standardize_input(df):
    df = df.copy()

    column_mapping = {
        "MAKE": "Make",
        "MODEL": "Model",
        "VEHICLE CLASS": "VEHICLE CLASS",
        "ENGINE SIZE": "ENGINE SIZE",
        "CYLINDERS": "CYLINDERS",
        "TRANSMISSION": "Transmission",
        "FUEL": "FUEL",
        "FUEL TYPE": "FUEL",
        "FUEL CONSUMPTION": "CITY (L/100 km)",
        "FUEL CONSUMPTION CITY (L/100 km)": "CITY (L/100 km)",
        "FUEL CONSUMPTION HWY (L/100 km)": "HWY (L/100 km)",
        "FUEL CONSUMPTION COMB (L/100 km)": "COMB (L/100 km)",
        "FUEL CONSUMPTION COMB (mpg)": "COMB (mpg)",
        "CO2 EMISSIONS (g/km)": "EMISSIONS",
        "Engine Type": "ENGINE TYPE",
        "YEAR": "YEAR",
    }
    df.rename(columns=column_mapping, inplace=True)

    numeric_cols = [
        "YEAR",
        "ENGINE SIZE",
        "CYLINDERS",
        "CITY (L/100 km)",
        "HWY (L/100 km)",
        "COMB (L/100 km)",
        "COMB (mpg)",
        "EMISSIONS",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Make" in df.columns:
        df["Make"] = df["Make"].apply(normalize_make)
    if "Model" in df.columns:
        df["Model"] = df["Model"].apply(normalize_model)
    if "VEHICLE CLASS" in df.columns:
        df["VEHICLE CLASS"] = df["VEHICLE CLASS"].apply(normalize_vehicle_class)
    if "Transmission" in df.columns:
        df["Transmission"] = df["Transmission"].apply(normalize_transmission)
    if "ENGINE TYPE" in df.columns:
        df["ENGINE TYPE"] = df["ENGINE TYPE"].apply(normalize_engine_type)
    if "FUEL" in df.columns:
        df["FUEL"] = df["FUEL"].apply(normalize_fuel)

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("UNKNOWN")

    numeric_df = df.select_dtypes(include="number")
    for col in numeric_df.columns:
        df[col] = df[col].fillna(df[col].median())

    df = add_proxy_features(df)
    return df

def analyze_user_requirements(requirement_text):
    text = requirement_text.lower()
    weights = {target: 0.0 for target in TARGET_KEYWORDS}

    for target, keywords in TARGET_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                weights[target] += 1.0

    if not any(weights.values()):
        weights["family_score"] = 1.0
        weights["economy_score"] = 1.0

    total = sum(weights.values())
    return {target: value / total for target, value in weights.items()}

def load_and_prepare_vehicle_data():
    raw_df = pd.read_csv(DATASET_PATH)
    raw_df = raw_df.drop_duplicates().reset_index(drop=True)
    prepared_df = standardize_input(raw_df.copy())
    prepared_df = prepared_df.loc[raw_df.index].copy()
    return raw_df, prepared_df

def infer_primary_need_from_weights(weights):
    need_targets = {
        "economy_score": "economy",
        "performance_score": "performance",
        "luxury_score": "luxury",
        "family_score": "family",
    }
    ranked_needs = sorted(
        need_targets.items(), key=lambda item: weights.get(item[0], 0.0), reverse=True
    )
    return ranked_needs[0][1] if ranked_needs and ranked_needs[0][1] else "economy"

def apply_profile_filters(raw_df, prepared_df, salary_level=None, year_min=None,
                          max_fuel_consumption=None, primary_need=None):
    filtered_raw = raw_df.copy()

    if salary_level:
        salary_key = str(salary_level).strip().lower()
        if salary_key in SALARY_YEAR_MAP:
            min_year, max_year = SALARY_YEAR_MAP[salary_key]
            filtered_raw = filtered_raw[filtered_raw["YEAR"].between(min_year, max_year)]

    if year_min is not None:
        filtered_raw = filtered_raw[filtered_raw["YEAR"] >= year_min]

    if max_fuel_consumption is not None and "COMB (L/100 km)" in filtered_raw.columns:
        comb_numeric = pd.to_numeric(filtered_raw["COMB (L/100 km)"], errors="coerce")
        mask = comb_numeric <= max_fuel_consumption
        filtered_raw = filtered_raw[mask.fillna(False)]

    if primary_need:
        need_key = str(primary_need).strip().lower()
        preferred_classes = PRIMARY_NEED_CLASS_MAP.get(need_key)
        if preferred_classes and "VEHICLE CLASS" in filtered_raw.columns:
            upper_classes = filtered_raw["VEHICLE CLASS"].astype(str).str.upper()
            mask = upper_classes.isin(preferred_classes)
            if mask.sum() > 0:
                filtered_raw = filtered_raw[mask]

    filtered_prepared = prepared_df.loc[filtered_raw.index].copy()
    return filtered_raw, filtered_prepared

def build_recommendation_table(models, metadata, salary_level=None, year_min=None,
                               max_fuel_consumption=None, primary_need=None):
    raw_df, prepared_df = load_and_prepare_vehicle_data()
    filtered_raw, filtered_prepared = apply_profile_filters(
        raw_df=raw_df,
        prepared_df=prepared_df,
        salary_level=salary_level,
        year_min=year_min,
        max_fuel_consumption=max_fuel_consumption,
        primary_need=primary_need,
    )

    if filtered_prepared.empty:
        raise ValueError("No vehicles matched the given salary/filter criteria.")

    feature_df = filtered_prepared[metadata["all_feature_columns"]].copy()
    scored_df = filtered_prepared.copy()

    for target, model in models.items():
        scored_df[target] = model.predict(feature_df)

    keep_columns = [
        "Make", "Model", "YEAR", "VEHICLE CLASS", "Transmission",
        "COMB (L/100 km)", "COMB (mpg)", "EMISSIONS",
    ]
    for col in keep_columns:
        if col in filtered_raw.columns:
            scored_df[col] = filtered_raw[col].values

    return scored_df

def recommend_vehicles_by_weights(weights, top_n=5, scored_df=None, models=None, metadata=None,
                                  salary_level=None, year_min=None,
                                  max_fuel_consumption=None, primary_need=None):
    if scored_df is None:
        if models is None or metadata is None:
            models, metadata = load_models()
        scored_df = build_recommendation_table(
            models=models,
            metadata=metadata,
            salary_level=salary_level,
            year_min=year_min,
            max_fuel_consumption=max_fuel_consumption,
            primary_need=primary_need,
        )

    ranked_df = scored_df.copy()
    ranked_df["final_recommendation_score"] = 0.0
    for target, weight in weights.items():
        ranked_df["final_recommendation_score"] += ranked_df[target] * weight

    ranked = ranked_df.sort_values("final_recommendation_score", ascending=False).head(top_n).copy()

    active_targets = [target for target, weight in weights.items() if weight > 0]
    ranked["best_match_reason"] = ranked[active_targets].idxmax(axis=1)

    output_cols = [
        "Make",
        "Model",
        "YEAR",
        "VEHICLE CLASS",
        "Transmission",
        "COMB (L/100 km)",
        "COMB (mpg)",
        "EMISSIONS",
        "final_recommendation_score",
        "best_match_reason",
    ]
    output_cols = [col for col in output_cols if col in ranked.columns]
    return ranked[output_cols]

def recommend_vehicles(requirement_text, top_n=5, salary_level=None,
                       year_min=None, max_fuel_consumption=None):
    models, metadata = load_models()
    weights = analyze_user_requirements(requirement_text)
    primary_need = infer_primary_need_from_weights(weights)
    scored_df = build_recommendation_table(
        models=models,
        metadata=metadata,
        salary_level=salary_level,
        year_min=year_min,
        max_fuel_consumption=max_fuel_consumption,
        primary_need=primary_need,
    )
    ranked = recommend_vehicles_by_weights(
        weights=weights,
        top_n=top_n,
        scored_df=scored_df,
    )
    return ranked, weights

def main():
    user_requirements = (
        "I need a family vehicle with good fuel economy for city driving "
        "and occasional highway trips."
    )

    salary_level = "medium"
    recommendations, weights = recommend_vehicles(
        user_requirements,
        top_n=5,
        salary_level=salary_level,
        year_min=2015,
        max_fuel_consumption=10,
    )

    print("\nUser requirement:")
    print(user_requirements)
    print(f"Salary level: {salary_level}")

    print("\nDetected requirement weights:")
    for target, weight in weights.items():
        if weight > 0:
            print(f"{target:20s}: {weight:.2f}")

    print("\nTop recommended vehicles:\n")
    print(recommendations.to_string(index=False))

if __name__ == "__main__":
    main()
