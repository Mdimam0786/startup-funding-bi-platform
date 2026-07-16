"""
Use Case 1: Funding Amount Prediction (Regression)
Predicts log_funding_total_usd from company profile features.
Compares Linear Regression (baseline) vs Random Forest vs XGBoost,
with 5-fold CV and randomized hyperparameter search on the best model.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

WH = str(Path(__file__).resolve().parents[2] / "data" / "warehouse") + "/"

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from data_prep import load_modeling_table, FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL

df = load_modeling_table()
model_df = df.dropna(subset=['log_funding_total_usd'] + FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL)
print(f"Modeling dataset: {len(model_df):,} rows")

X = model_df[FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL]
y = model_df['log_funding_total_usd']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), FEATURE_COLS_CATEGORICAL),
], remainder='passthrough')


def evaluate(name, pipeline):
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='r2')
    print(f"\n{name}")
    print(f"  Test MAE: {mae:.3f} (log scale) | RMSE: {rmse:.3f} | R2: {r2:.3f}")
    print(f"  5-fold CV R2: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    return {'name': name, 'mae': mae, 'rmse': rmse, 'r2': r2, 'cv_r2_mean': cv_scores.mean(), 'cv_r2_std': cv_scores.std(), 'pipeline': pipeline}

print("\n"+"="*80); print("MODEL COMPARISON"); print("="*80)

results = []
results.append(evaluate("Linear Regression (baseline)", Pipeline([('prep', preprocessor), ('model', LinearRegression())])))
results.append(evaluate("Random Forest (default)", Pipeline([('prep', preprocessor), ('model', RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1))])))
results.append(evaluate("XGBoost (default)", Pipeline([('prep', preprocessor), ('model', xgb.XGBRegressor(n_estimators=150, random_state=42, n_jobs=-1))])))

print("\n"+"="*80); print("HYPERPARAMETER TUNING: XGBoost (RandomizedSearchCV, 5-fold)"); print("="*80)
param_dist = {
    'model__n_estimators': [100, 200, 300],
    'model__max_depth': [3, 4, 5, 6],
    'model__learning_rate': [0.03, 0.05, 0.1],
    'model__subsample': [0.8, 0.9, 1.0],
    'model__colsample_bytree': [0.8, 0.9, 1.0],
}
xgb_pipeline = Pipeline([('prep', preprocessor), ('model', xgb.XGBRegressor(random_state=42, n_jobs=-1))])
search = RandomizedSearchCV(xgb_pipeline, param_dist, n_iter=10, cv=5, scoring='r2', random_state=42, n_jobs=-1)
search.fit(X_train, y_train)
print(f"Best params: {search.best_params_}")
print(f"Best CV R2: {search.best_score_:.3f}")

best_model = search.best_estimator_
preds = best_model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))
r2 = r2_score(y_test, preds)
print(f"\nTuned XGBoost on held-out test set: MAE={mae:.3f}, RMSE={rmse:.3f}, R2={r2:.3f}")
results.append({'name': 'XGBoost (tuned)', 'mae': mae, 'rmse': rmse, 'r2': r2, 'cv_r2_mean': search.best_score_, 'cv_r2_std': np.nan, 'pipeline': best_model})

print("\n"+"="*80); print("MODEL COMPARISON SUMMARY"); print("="*80)
summary = pd.DataFrame([{k: v for k, v in r.items() if k != 'pipeline'} for r in results])
print(summary.to_string(index=False))

# Feature importance from the tuned XGBoost model
feature_names = (best_model.named_steps['prep'].named_transformers_['cat'].get_feature_names_out(FEATURE_COLS_CATEGORICAL).tolist()
                  + FEATURE_COLS_NUMERIC)
importances = best_model.named_steps['model'].feature_importances_
imp_df = pd.DataFrame({'feature': feature_names, 'importance': importances}).sort_values('importance', ascending=False)
print("\nTop 15 feature importances (tuned XGBoost):")
print(imp_df.head(15).to_string(index=False))

# Save the model + test set for the explainability (SHAP) script
import joblib
joblib.dump(best_model, WH + 'regression_model.pkl')
X_test.to_csv(WH + 'regression_X_test.csv', index=False,encoding="utf-8")
y_test.to_csv(WH + 'regression_y_test.csv', index=False,encoding="utf-8")
imp_df.to_csv(WH + 'regression_feature_importance.csv', index=False,encoding="utf-8")
summary.to_csv(WH + 'regression_model_comparison.csv', index=False,encoding="utf-8")
print("\nSaved model, test set, and importance table for SHAP script.")
