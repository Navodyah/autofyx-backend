"""
Maintenance Cost Range Prediction Model
This script demonstrates how to build a machine learning model to predict
vehicle maintenance cost ranges.
"""

import warnings
import joblib


import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


warnings.filterwarnings('ignore')

# ============================================================================
# STEP 1: DATA LOADING AND EXPLORATION
# ============================================================================
print("=" * 70)
print("STEP 1: LOADING AND EXPLORING DATA")
print("=" * 70)

df = pd.read_csv('maintain_data.csv')

print(f"\nDataset Shape: {df.shape}")
print(f"\nColumn Names and Types:")
print(df.dtypes)
print(f"\nFirst 5 rows:")
print(df.head())
print(f"\nMaintenance Cost Statistics:")
print(df['Maintenance Cost'].describe())

# ============================================================================
# STEP 2: DEFINE MAINTENANCE COST RANGES
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: CREATING COST RANGES (Classification)")
print("=" * 70)

# Define cost ranges based on quartiles
Q1 = df['Maintenance Cost'].quantile(0.25)
Q2 = df['Maintenance Cost'].quantile(0.5)
Q3 = df['Maintenance Cost'].quantile(0.75)

print(f"\nQuartile Breakdown:")
print(f"Q1 (25%): ${Q1:,.0f}")
print(f"Q2 (50%): ${Q2:,.0f}")
print(f"Q3 (75%): ${Q3:,.0f}")

# Create cost range categories
def assign_cost_range(cost):
    if cost <= Q1:
        return 'Very Low (Under ${:,.0f})'.format(Q1)
    elif cost <= Q2:
        return 'Low (${:,.0f} - ${:,.0f})'.format(Q1, Q2)
    elif cost <= Q3:
        return 'Medium (${:,.0f} - ${:,.0f})'.format(Q2, Q3)
    else:
        return 'High (Over ${:,.0f})'.format(Q3)

df['Cost_Range'] = df['Maintenance Cost'].apply(assign_cost_range)

print(f"\nCost Range Distribution:")
print(df['Cost_Range'].value_counts())

# ============================================================================
# STEP 3: DATA PREPROCESSING
# ============================================================================
print("\n" + "=" * 70)
print("STEP 3: DATA PREPROCESSING")
print("=" * 70)

# Check for missing values
print(f"\nMissing Values:")
print(df.isnull().sum())

# Identify numerical and categorical features
categorical_cols = df.select_dtypes(include='object').columns.tolist()
numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

# Remove the target column from lists
if 'Maintenance Cost' in numerical_cols:
    numerical_cols.remove('Maintenance Cost')
if 'Cost_Range' in categorical_cols:
    categorical_cols.remove('Cost_Range')

print(f"\nNumerical Features: {numerical_cols}")
print(f"Categorical Features: {categorical_cols}")

# ============================================================================
# STEP 4: FEATURE ENCODING
# ============================================================================
print("\n" + "=" * 70)
print("STEP 4: ENCODING CATEGORICAL FEATURES")
print("=" * 70)

df_processed = df.copy()

# Encode categorical variables
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df_processed[col + '_encoded'] = le.fit_transform(df_processed[col])
    label_encoders[col] = le
    print(f"\n{col} encoding:")
    for i, class_name in enumerate(le.classes_):
        print(f"  {i}: {class_name}")

# Create feature matrix (X) with encoded features
feature_cols = numerical_cols + [col + '_encoded' for col in categorical_cols]
X = df_processed[feature_cols].copy()
y_regression = df_processed['Maintenance Cost'].copy()

# For classification, encode the cost ranges
le_cost_range = LabelEncoder()
y_classification = le_cost_range.fit_transform(df_processed['Cost_Range'])

print(f"\nCost Range Classes:")
for i, range_name in enumerate(le_cost_range.classes_):
    print(f"  {i}: {range_name}")

print(f"\nFeature Matrix Shape: {X.shape}")
print(f"Number of Features: {X.shape[1]}")

# ============================================================================
# STEP 5: TRAIN-TEST SPLIT
# ============================================================================
print("\n" + "=" * 70)
print("STEP 5: TRAIN-TEST SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_regression, test_size=0.2, random_state=42
)

print(f"Training Set Size: {X_train.shape[0]} samples")
print(f"Testing Set Size: {X_test.shape[0]} samples")

# ============================================================================
# STEP 6: FEATURE SCALING
# ============================================================================
print("\n" + "=" * 70)
print("STEP 6: FEATURE SCALING")
print("=" * 70)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Features have been standardized (mean=0, std=1)")

# ============================================================================
# STEP 7: MODEL TRAINING (REGRESSION)
# ============================================================================
print("\n" + "=" * 70)
print("STEP 7: TRAINING REGRESSION MODELS")
print("=" * 70)

# Model 1: Random Forest
print("\n[1] Random Forest Regressor")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_r2 = r2_score(y_test, rf_pred)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
rf_mae = mean_absolute_error(y_test, rf_pred)

print(f"  R² Score: {rf_r2:.4f}")
print(f"  RMSE: ${rf_rmse:,.2f}")
print(f"  MAE: ${rf_mae:,.2f}")

# Model 2: Gradient Boosting
print("\n[2] Gradient Boosting Regressor")
gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
gb_model.fit(X_train, y_train)
gb_pred = gb_model.predict(X_test)
gb_r2 = r2_score(y_test, gb_pred)
gb_rmse = np.sqrt(mean_squared_error(y_test, gb_pred))
gb_mae = mean_absolute_error(y_test, gb_pred)

print(f"  R² Score: {gb_r2:.4f}")
print(f"  RMSE: ${gb_rmse:,.2f}")
print(f"  MAE: ${gb_mae:,.2f}")

# Model 3: Linear Regression (Baseline)
print("\n[3] Linear Regression (Baseline)")
lr_model = LinearRegression()
lr_model.fit(X_train_scaled, y_train)
lr_pred = lr_model.predict(X_test_scaled)
lr_r2 = r2_score(y_test, lr_pred)
lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
lr_mae = mean_absolute_error(y_test, lr_pred)

print(f"  R² Score: {lr_r2:.4f}")
print(f"  RMSE: ${lr_rmse:,.2f}")
print(f"  MAE: ${lr_mae:,.2f}")

# ============================================================================
# STEP 8: BEST MODEL & COST RANGE PREDICTION
# ============================================================================
print("\n" + "=" * 70)
print("STEP 8: BEST MODEL SUMMARY")
print("=" * 70)

best_r2 = max(rf_r2, gb_r2, lr_r2)
if best_r2 == rf_r2:
    best_model = rf_model
    best_model_name = "Random Forest"
elif best_r2 == gb_r2:
    best_model = gb_model
    best_model_name = "Gradient Boosting"
else:
    best_model = lr_model
    best_model_name = "Linear Regression"
    X_test = X_test_scaled  # Use scaled features for prediction

print(f"\nBest Model: {best_model_name}")
print(f"R² Score: {best_r2:.4f}")

# ============================================================================
# STEP 9: FEATURE IMPORTANCE (For tree-based models)
# ============================================================================
if best_model_name != "Linear Regression":
    print("\n" + "=" * 70)
    print("STEP 9: FEATURE IMPORTANCE")
    print("=" * 70)

    feature_importance = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': best_model.feature_importances_
    }).sort_values('Importance', ascending=False)

    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

# ============================================================================
# STEP 10: PREDICTION EXAMPLE
# ============================================================================
print("\n" + "=" * 70)
print("STEP 10: EXAMPLE PREDICTION")
print("=" * 70)

# Take a sample from test set
sample_idx = 0
sample_features = X_test.iloc[sample_idx:sample_idx+1]
actual_cost = y_test.iloc[sample_idx]

predicted_cost = best_model.predict(sample_features)[0]

if predicted_cost <= Q1:
    predicted_range = 'Very Low (Under ${:,.0f})'.format(Q1)
elif predicted_cost <= Q2:
    predicted_range = 'Low (${:,.0f} - ${:,.0f})'.format(Q1, Q2)
elif predicted_cost <= Q3:
    predicted_range = 'Medium (${:,.0f} - ${:,.0f})'.format(Q2, Q3)
else:
    predicted_range = 'High (Over ${:,.0f})'.format(Q3)

print(f"\nSample Vehicle:")
print(f"  Actual Maintenance Cost: ${actual_cost:,.0f}")
print(f"  Predicted Maintenance Cost: ${predicted_cost:,.0f}")
print(f"  Predicted Cost Range: {predicted_range}")
print(f"  Error: ${abs(actual_cost - predicted_cost):,.0f}")

# Save model
joblib.dump(best_model, "maintenance_model.pkl")

# Save scaler
joblib.dump(scaler, "scaler.pkl")

# Save label encoders
joblib.dump(label_encoders, "encoders.pkl")

print("Model saved successfully!")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("SUMMARY & NEXT STEPS")
print("=" * 70)
print(f"""
1. ✓ Loaded dataset with {df.shape[0]} vehicles
2. ✓ Created 4 cost ranges based on quartiles
3. ✓ Processed {len(feature_cols)} features
4. ✓ Trained 3 regression models
5. ✓ Best Model: {best_model_name} (R² = {best_r2:.4f})

RECOMMENDED NEXT STEPS:
- Hyperparameter tuning (GridSearchCV, RandomizedSearchCV)
- Cross-validation for better generalization
- Feature engineering (create new features from existing ones)
- Handling outliers in maintenance costs
- Regular model retraining with new data

DEPLOYMENT:
- Save the trained model using joblib or pickle
- Create an API endpoint for predictions
- Monitor model performance on new data
""")

print("=" * 70)

