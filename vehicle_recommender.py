"""
Vehicle Recommendation System - User Interface
Get personalized vehicle recommendations based on your preferences
"""

import warnings
from typing import Dict

import joblib
import os
import pandas as pd

warnings.filterwarnings('ignore')

class VehicleRecommender:
    def __init__(self):
        self.models = joblib.load("vehicle_ranking_models.pkl")
        self.label_encoders = joblib.load("vehicle_label_encoders.pkl")
        self.feature_cols = joblib.load("vehicle_feature_columns.pkl")
        self.vehicle_data = None
        self.models_dir = "trained_models"

    def load_vehicle_inventory(self, filepath):
        """Load vehicle data from CSV"""
        df = pd.read_csv(filepath)

        # Convert numeric columns from strings to numbers
        numeric_cols = ["YEAR", "ENGINE SIZE", "CYLINDERS", "COMB (L/100 km)",
                        "COMB (mpg)", "HWY (L/100 km)", "FUEL CONSUMPTION HWY (L/100 km)", "EMISSIONS"]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Store original data before encoding
        self.original_data = df.copy()

        # Prepare and store engineered data
        df = self._prepare_vehicle_data(df)
        self.vehicle_data = df
        print(f"✅ Loaded {len(df)} vehicles from inventory")

    def _prepare_vehicle_data(self, df):
        """Apply same feature engineering as training"""

        # Define expected numeric columns
        numeric_cols = ["YEAR", "ENGINE SIZE", "CYLINDERS", "COMB (L/100 km)",
                        "COMB (mpg)", "HWY (L/100 km)", "FUEL CONSUMPTION HWY (L/100 km)", "EMISSIONS"]

        # Convert numeric columns first
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Fill missing values - separate handling for numeric and categorical
        for col in df.columns:
            if col in numeric_cols:
                # Only fill numeric columns with median
                if df[col].notna().any():
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(0, inplace=True)
            elif df[col].dtype == "object":
                # Fill categorical columns with "Unknown"
                df[col].fillna("Unknown", inplace=True)

        # Rest of the code remains the same...
        # Engine features
        def map_engine_features(e):
            if e == "I":
                return pd.Series([5, 2, 5])
            elif e == "V":
                return pd.Series([9, 8, 3])
            else:
                return pd.Series([5, 5, 5])

        df[["engine_power_score", "engine_maintenance_cost", "engine_efficiency_score"]] = \
            df["Engine Type"].apply(map_engine_features)

        # ... continue with rest of the method

        # Transmission features
        def map_transmission(t):
            if t == "A":
                return pd.Series([8, 8, 8])
            elif t == "AM":
                return pd.Series([6, 5, 7])
            elif t == "AS":
                return pd.Series([9, 7, 10])
            elif t == "AV":
                return pd.Series([4, 3, 4])
            else:
                return pd.Series([5, 5, 5])

        df[["trans_performance_score", "trans_maintenance_score", "driving_pleasure_score"]] = \
            df["TRANSMISSION"].apply(map_transmission)

        # Brand features
        def brand_scores(make):
            make = str(make).lower()
            if any(b in make for b in ["toyota", "nissan", "honda", "lexus", "mazda", "suzuki", "mitsubishi"]):
                return pd.Series([9, 2, 6])
            if any(b in make for b in ["bmw", "benz", "mercedes", "audi"]):
                return pd.Series([9, 9, 9])
            if any(b in make for b in ["ford", "chevrolet", "dodge", "gmc"]):
                return pd.Series([7, 5, 8])
            return pd.Series([6, 5, 5])

        df[["brand_reliability_score", "brand_maintenance_cost", "brand_performance_bias"]] = \
            df["MAKE"].apply(brand_scores)

        # Fuel type features
        def fuel_type_score(fuel):
            fuel = str(fuel).upper()
            if fuel == "X":
                return pd.Series([5, 5])  # cost_score, availability_score
            elif fuel == "Z":
                return pd.Series([8, 6])  # Premium gasoline - higher cost
            elif fuel == "D":
                return pd.Series([3, 7])  # Diesel - lower cost
            else:
                return pd.Series([5, 5])  # Default

        df[["fuel_cost_score", "fuel_availability_score"]] = \
            df["FUEL"].apply(fuel_type_score)

        # Calculated features
        # Ensure numeric type first
        df["COMB (L/100 km)"] = pd.to_numeric(df["COMB (L/100 km)"], errors='coerce')
        df["EMISSIONS"] = pd.to_numeric(df["EMISSIONS"], errors='coerce')

        df["fuel_efficiency_score"] = 100 / (df["COMB (L/100 km)"] + 1)
        df["emission_score"] = 100 / (df["EMISSIONS"] + 1)
        df["power_to_size_ratio"] = df["CYLINDERS"] / (df["ENGINE SIZE"] + 0.1)
        df["estimated_price_category"] = (
            (df["YEAR"] - 2000) * 0.2 +
            df["CYLINDERS"] * 0.8 +
            df["ENGINE SIZE"] * 1.5 +
            df["brand_performance_bias"] * 0.5
        ).clip(0, 10)

        # Encode categorical
        for col in ["MAKE", "MODEL", "VEHICLE CLASS", "Engine Type", "TRANSMISSION", "FUEL"]:
            if col in df.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                df[col] = df[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )

        return df

    def get_recommendations(self, user_profile: Dict, top_n: int = 10) -> pd.DataFrame:
        """
        Get vehicle recommendations based on user profile

        Parameters:
        -----------
        user_profile : dict
            {
                'salary_level': 'low'|'medium'|'high'|'luxury',  # Budget level
                'primary_need': 'economy'|'performance'|'luxury'|'family',  # Main priority
                'usage': 'city'|'highway'|'mixed'|'off-road',  # Primary usage
                'year_min': 2015,  # Optional: minimum year
                'max_fuel_consumption': 10,  # Optional: max L/100km
            }
        top_n : int
            Number of recommendations to return
        """

        if self.vehicle_data is None:
            raise ValueError("Please load vehicle inventory first using load_vehicle_inventory()")

        print("=" * 70)
        print("🚗 VEHICLE RECOMMENDATION ENGINE")
        print("=" * 70)
        print()
        print("User Profile:")
        print(f"  💰 Salary Level: {user_profile.get('salary_level', 'medium').upper()}")
        print(f"  🎯 Primary Need: {user_profile.get('primary_need', 'economy').upper()}")
        print(f"  🛣️  Usage Type: {user_profile.get('usage', 'mixed').upper()}")
        print()

        # Apply filters
        filtered_df = self._apply_filters(user_profile)
        print(f"📊 Found {len(filtered_df)} vehicles matching your criteria")
        print()

        # Calculate ranking scores
        scores_df = self._calculate_ranking_scores(filtered_df, user_profile)

        # Get top recommendations
        top_recommendations = scores_df.nlargest(top_n, 'final_score')

        # Prepare output
        result_df = self._prepare_output(top_recommendations)

        return result_df

    def _apply_filters(self, user_profile: Dict) -> pd.DataFrame:
        """Apply basic filters based on user profile"""
        original = self.original_data.copy()

        # Salary-based price filtering (using year as proxy for price)
        salary_map = {
            'low': (2000, 2015),
            'medium': (2010, 2020),
            'high': (2015, 2024),
            'luxury': (2018, 2024)
        }
        salary = user_profile.get('salary_level', 'medium')
        if salary in salary_map:
            year_min, year_max = salary_map[salary]
            original = original[original['YEAR'].between(year_min, year_max)]

        # Year filter (override salary-based year if specified)
        if 'year_min' in user_profile:
            year_min = user_profile['year_min']
            original = original[original['YEAR'] >= year_min]

        # Fuel consumption filter
        if 'max_fuel_consumption' in user_profile:
            max_fuel = user_profile['max_fuel_consumption']
            original = original[original['COMB (L/100 km)'] <= max_fuel]

        # Vehicle class preferences based on primary need
        need = user_profile.get('primary_need', 'economy')
        if need == 'family':
            # Prefer larger vehicles
            preferred_classes = ['MID-SIZE', 'SUV - SMALL', 'SUV - STANDARD', 'MINIVAN']
            mask = original['VEHICLE CLASS'].str.upper().isin(preferred_classes)
            if mask.sum() > 0:
                original = original[mask]

        # Return corresponding encoded data
        return self.vehicle_data.loc[original.index]

    def _calculate_ranking_scores(self, df: pd.DataFrame, user_profile: Dict) -> pd.DataFrame:
        """Calculate ranking scores using trained models"""

        X = df[self.feature_cols]

        # Get primary need and usage
        primary_need = user_profile.get('primary_need', 'economy')
        usage = user_profile.get('usage', 'mixed')

        # Map needs to score types
        need_score_map = {
            'economy': 'economy_score',
            'performance': 'performance_score',
            'luxury': 'luxury_score',
            'family': 'family_score'
        }

        usage_score_map = {
            'city': 'city_score',
            'highway': 'highway_score',
            'mixed': None,  # Use average of city and highway
            'off-road': 'performance_score'  # Use performance as proxy
        }

        # Predict scores
        need_score_type = need_score_map.get(primary_need, 'economy_score')
        usage_score_type = usage_score_map.get(usage)

        need_scores = self.models[need_score_type].predict(X)

        if usage_score_type:
            usage_scores = self.models[usage_score_type].predict(X)
        else:
            # Mixed usage - average city and highway
            city_scores = self.models['city_score'].predict(X)
            highway_scores = self.models['highway_score'].predict(X)
            usage_scores = (city_scores + highway_scores) / 2

        # Combine scores (70% need, 30% usage)
        final_scores = need_scores * 0.7 + usage_scores * 0.3

        df = df.copy()
        df['need_score'] = need_scores
        df['usage_score'] = usage_scores
        df['final_score'] = final_scores

        return df

    def _prepare_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare user-friendly output"""

        # Get original data for these indices
        original = self.original_data.loc[df.index].copy()

        # Add scores
        original['Compatibility_Score'] = df['final_score'].round(1)
        original['Need_Match'] = df['need_score'].round(1)
        original['Usage_Match'] = df['usage_score'].round(1)

        # Reorder columns for display
        display_cols = [
            'YEAR', 'MAKE', 'MODEL', 'VEHICLE CLASS',
            'ENGINE SIZE', 'CYLINDERS', 'TRANSMISSION', 'FUEL',
            'COMB (L/100 km)', 'COMB (mpg)', 'EMISSIONS',
            'Compatibility_Score', 'Need_Match', 'Usage_Match'
        ]

        result = original[display_cols].reset_index(drop=True)
        result.index = result.index + 1  # Start from 1

        return result

    def save_models(self, directory=None):
        """Save trained models to disk"""
        if directory is None:
            directory = self.models_dir

        os.makedirs(directory, exist_ok=True)

        joblib.dump(self.scaler, os.path.join(directory, "scaler.pkl"))
        joblib.dump(self.knn_model, os.path.join(directory, "knn_model.pkl"))
        joblib.dump(self.feature_matrix, os.path.join(directory, "feature_matrix.pkl"))
        joblib.dump(self.label_encoders, os.path.join(directory, "label_encoders.pkl"))
        print(f"✅ Models saved to {directory}/")

    def load_models(self, directory=None):
        """Load pre-trained models from disk"""
        if directory is None:
            directory = self.models_dir

        self.scaler = joblib.load(os.path.join(directory, "scaler.pkl"))
        self.knn_model = joblib.load(os.path.join(directory, "knn_model.pkl"))
        self.feature_matrix = joblib.load(os.path.join(directory, "feature_matrix.pkl"))
        self.label_encoders = joblib.load(os.path.join(directory, "label_encoders.pkl"))
        print(f"✅ Models loaded from {directory}/")


def main():
    """Example usage"""

    # Initialize recommender
    recommender = VehicleRecommender()
    recommender.load_vehicle_inventory("vehicledata.csv")
    print()

    # Example 1: Budget-conscious city driver
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Budget-Conscious City Driver")
    print("=" * 70)
    user1 = {
        'salary_level': 'low',
        'primary_need': 'economy',
        'usage': 'city',
        'year_min': 2015,
        'max_fuel_consumption': 7
    }
    recommendations1 = recommender.get_recommendations(user1, top_n=5)
    print("\n🏆 TOP 5 RECOMMENDATIONS:\n")
    print(recommendations1.to_string())
    print()

    # Example 2: Performance enthusiast
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Performance Enthusiast")
    print("=" * 70)
    user2 = {
        'salary_level': 'high',
        'primary_need': 'performance',
        'usage': 'highway',
        'year_min': 2018
    }
    recommendations2 = recommender.get_recommendations(user2, top_n=5)
    print("\n🏆 TOP 5 RECOMMENDATIONS:\n")
    print(recommendations2.to_string())
    print()

    # Example 3: Family person
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Family-Oriented Buyer")
    print("=" * 70)
    user3 = {
        'salary_level': 'medium',
        'primary_need': 'family',
        'usage': 'mixed',
        'year_min': 2016,
        'max_fuel_consumption': 10
    }
    recommendations3 = recommender.get_recommendations(user3, top_n=5)
    print("\n🏆 TOP 5 RECOMMENDATIONS:\n")
    print(recommendations3.to_string())
    print()


if __name__ == "__main__":
    main()