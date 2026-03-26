"""
Vehicle Recommendation System - User Interface
Get personalized vehicle recommendations based on your preferences
"""

import pandas as pd
import numpy as np
import joblib
from typing import Dict
import warnings

warnings.filterwarnings('ignore')


class VehicleRecommender:
    def __init__(self):
        self.models = joblib.load("vehicle_ranking_models.pkl")
        self.label_encoders = joblib.load("vehicle_label_encoders.pkl")
        self.feature_cols = joblib.load("vehicle_feature_columns.pkl")
        self.vehicle_data = None

    def load_vehicle_inventory(self, filepath):
        """Load vehicle data from CSV"""
        df = pd.read_csv(filepath)

        # Rename columns for consistency (same as training)
        column_mapping = {
            'Engine Type': 'ENGINE TYPE',
            'TRANSMISSION': 'Transmission',
            'MAKE': 'Make',
            'MODEL': 'Model'
        }
        df = df.rename(columns=column_mapping)

        # Convert numeric columns from strings to numbers
        numeric_cols = ["YEAR", "ENGINE SIZE", "CYLINDERS", "COMB (L/100 km)",
                        "COMB (mpg)", "HWY (L/100 km)", "EMISSIONS"]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Add HORSEPOWER estimate if not present
        if 'HORSEPOWER' not in df.columns:
            df['HORSEPOWER'] = df['ENGINE SIZE'] * df['CYLINDERS'] * 20

        # Add MAINTENANCE COST estimate if not present
        if 'MAINTENANCE COST' not in df.columns:
            base_cost = 50000
            df['MAINTENANCE COST'] = (
                    base_cost +
                    df['ENGINE SIZE'] * 30000 +
                    df['CYLINDERS'] * 15000 +
                    (2024 - df['YEAR']) * 5000
            )

        # Store original data before encoding
        self.original_data = df.copy()

        # Prepare and store engineered data
        df = self._prepare_vehicle_data(df)
        self.vehicle_data = df
        print(f"✅ Loaded {len(df)} vehicles from inventory")

    def _prepare_vehicle_data(self, df):
        """Apply same feature engineering as training"""

        # Fill missing values
        for col in df.columns:
            if df[col].dtype in ["object", "string"]:
                df[col].fillna("Unknown", inplace=True)
            elif pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True)

        # Engine features (same as training)
        def map_engine_features(e):
            if e == "I":
                return pd.Series([1.7, 0.7, 6.8])
            elif e == "V":
                return pd.Series([6.4, 3.4, 2.0])
            elif e == "W":
                return pd.Series([10.0, 10.0, 2.4])
            else:
                return pd.Series([3.0, 2.0, 4.0])

        df[["engine_power_score", "engine_maintenance_cost", "engine_efficiency_score"]] = \
            df["ENGINE TYPE"].apply(map_engine_features)

        # Transmission features (same as training)
        def map_transmission(t):
            t_upper = str(t).upper()
            if 'CVT' in t_upper:
                return pd.Series([1.5, 0.5, 3.7])
            elif 'AMT' in t_upper or 'AGS' in t_upper:
                return pd.Series([0.2, 0.1, 3.3])
            elif 'DCT' in t_upper or 'DSG' in t_upper or 'PDK' in t_upper or 'S-TRONIC' in t_upper:
                return pd.Series([4.6, 3.0, 4.8])
            elif 'MANUAL' in t_upper:
                return pd.Series([2.1, 1.0, 4.0])
            elif 'SINGLE' in t_upper:
                return pd.Series([1.5, 0.3, 4.0])
            else:
                return pd.Series([3.5, 1.8, 4.0])

        df[["trans_performance_score", "trans_maintenance_score", "driving_pleasure_score"]] = \
            df["Transmission"].apply(map_transmission)

        # Brand features (same as training)
        def brand_scores(make):
            make = str(make).lower()
            if any(b in make for b in ["toyota", "nissan", "honda", "lexus", "mazda",
                                       "suzuki", "mitsubishi", "subaru", "daihatsu",
                                       "isuzu", "perodua"]):
                return pd.Series([7.7, 0.9, 2.6])
            elif any(b in make for b in ["bmw", "benz", "mercedes", "audi", "volkswagen", "porsche"]):
                return pd.Series([2.9, 3.3, 4.9])
            elif any(b in make for b in ["ford", "chevrolet", "dodge", "gmc"]):
                return pd.Series([9.0, 0.2, 0.7])
            elif any(b in make for b in ["land rover", "range rover", "jaguar"]):
                return pd.Series([3.5, 3.0, 5.4])
            elif any(b in make for b in ["volvo", "peugeot", "renault", "citroen"]):
                return pd.Series([7.7, 0.9, 1.8])
            elif any(b in make for b in ["ferrari", "lamborghini", "maserati", "alfa"]):
                return pd.Series([1.5, 7.0, 9.5])
            elif any(b in make for b in ["hyundai", "kia", "genesis"]):
                return pd.Series([8.0, 1.2, 2.0])
            else:
                return pd.Series([6.5, 1.5, 1.5])

        df[["brand_reliability_score", "brand_maintenance_cost", "brand_performance_bias"]] = \
            df["Make"].apply(brand_scores)

        # Calculated features (same as training)
        df["fuel_efficiency_score"] = 100 / (df["COMB (L/100 km)"] + 1)
        df["emission_score"] = 100 / (df["EMISSIONS"] + 1)
        df["power_to_size_ratio"] = df["HORSEPOWER"] / (df["ENGINE SIZE"] + 0.1)

        # Estimated price category
        if 'MAINTENANCE COST' in df.columns:
            df["estimated_price_category"] = (
                    (df["MAINTENANCE COST"] / 100000) * 3 +
                    (df["HORSEPOWER"] / 100) * 2 +
                    df["brand_performance_bias"] * 0.5 +
                    df["engine_power_score"] * 0.3
            ).clip(0, 10)
        else:
            df["estimated_price_category"] = (
                    (df["YEAR"] - 2000) * 0.2 +
                    df["CYLINDERS"] * 0.8 +
                    df["ENGINE SIZE"] * 1.5 +
                    df["brand_performance_bias"] * 0.5
            ).clip(0, 10)

        # Encode categorical
        for col in ["Make", "Model", "VEHICLE CLASS", "ENGINE TYPE", "Transmission"]:
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
        """Apply basic filters based on user profile using actual Price Categories"""
        original = self.original_data.copy()

        # 1. Salary-based price filtering (Using estimated_price_category instead of YEAR)
        salary = user_profile.get('salary_level', 'medium')

        # 0 to 10 scale based on maintenance, HP, brand, etc.
        price_map = {
            'low': (0.0, 4.0),  # Budget friendly cars
            'medium': (2.5, 6.5),  # Mid-range cars
            'high': (5.0, 8.5),  # Expensive cars
            'luxury': (7.5, 10.0)  # Premium/Luxury cars
        }

        if salary in price_map and 'estimated_price_category' in self.vehicle_data.columns:
            min_price, max_price = price_map[salary]

            # Find indices of vehicles that fit the user's budget
            valid_indices = self.vehicle_data[
                self.vehicle_data['estimated_price_category'].between(min_price, max_price)
            ].index

            mask = original.index.isin(valid_indices)
            if mask.sum() > 0:
                original = original[mask]
            else:
                print(f"⚠️ No vehicles strictly found for '{salary}' budget, relaxing filter...")

        # 2. Year filter (override if specific year is given)
        if 'year_min' in user_profile:
            year_min = user_profile['year_min']
            mask = original['YEAR'] >= year_min
            if mask.sum() > 0:
                original = original[mask]

        # 3. Fuel consumption filter
        if 'max_fuel_consumption' in user_profile:
            max_fuel = user_profile['max_fuel_consumption']
            mask = original['COMB (L/100 km)'] <= max_fuel
            if mask.sum() > 0:
                original = original[mask]

        # 4. Vehicle class preferences based on primary need
        need = user_profile.get('primary_need', 'economy')
        if need == 'family':
            preferred_classes = ['MID-SIZE', 'SUV - SMALL', 'SUV - STANDARD', 'MINIVAN',
                                 'SUV', 'CROSSOVER', 'STATION WAGON', 'FULL-SIZE',
                                 'COMPACT', 'SUBCOMPACT']
            mask = original['VEHICLE CLASS'].str.upper().isin(preferred_classes)
            if mask.sum() > 0:
                original = original[mask]

        # Fallback: if all filters removed everything, return full dataset
        if original.empty:
            print("⚠️ No vehicles matched filters, relaxing all constraints...")
            return self.vehicle_data.copy()

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

        # Reorder columns for display (use renamed column names)
        display_cols = [
            'YEAR', 'Make', 'Model', 'VEHICLE CLASS',
            'ENGINE SIZE', 'CYLINDERS', 'Transmission', 'FUEL',
            'COMB (L/100 km)', 'COMB (mpg)', 'EMISSIONS',
            'Compatibility_Score', 'Need_Match', 'Usage_Match'
        ]

        result = original[display_cols].reset_index(drop=True)
        result.index = result.index + 1  # Start from 1

        return result


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
    recommendations1 = recommender.get_recommendations(user1, top_n=10)
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
    recommendations2 = recommender.get_recommendations(user2, top_n=10)
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
    recommendations3 = recommender.get_recommendations(user3, top_n=10)
    print("\n🏆 TOP 5 RECOMMENDATIONS:\n")
    print(recommendations3.to_string())
    print()


if __name__ == "__main__":
    main()