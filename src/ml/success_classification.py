"""
Use Case 2: Startup Success Classification
Target: is_exited (1 = reached IPO or acquisition, 0 = otherwise).
Compares Logistic Regression (baseline) vs Random Forest vs XGBoost,
with class imbalance handled explicitly (only ~11% positive class).
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

WH = str(Path(__file__).resolve().parents[2] / "data" / "warehouse") + "/"

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                              roc_auc_score, confusion_matrix, classification_report)
import xgboost as xgb
import joblib

from data_prep import load_modeling_table, FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL

df = load_modeling_table()
# Exclude funding_total_usd itself as a raw feature to keep this genuinely
# predictive (funding amount is downstream of many of the same decisions
# that drive exits) -- but DO keep the engineered funding-behavior features
# (rounds, multi-round, round-type diversity), which are legitimate
# early/mid-lifecycle signals a VC would actually have at decision time.
model_df = df.dropna(subset=['is_exited'] + FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL)
print(f"Modeling dataset: {len(model_df):,} rows")
print(f"Positive class (is_exited) rate: {model_df['is_exited'].mean()*100:.2f}%")

X = model_df[FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL]
y = model_df['is_exited'].astype(int)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")
print(f"Train positive rate: {y_train.mean()*100:.2f}% | Test positive rate: {y_test.mean()*100:.2f}%")

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), FEATURE_COLS_CATEGORICAL),
], remainder='passthrough')

# Class weight to address the ~11%/89% imbalance -- without this, a model
# can hit ~89% "accuracy" by just predicting "not exited" for everyone,
# which is useless. class_weight='balanced' / scale_pos_weight fixes this.
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"scale_pos_weight (for XGBoost imbalance handling): {scale_pos_weight:.2f}")


def evaluate(name, pipeline):
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    rec = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='roc_auc')
    print(f"\n{name}")
    print(f"  Accuracy: {acc:.3f} | Precision: {prec:.3f} | Recall: {rec:.3f} | F1: {f1:.3f} | ROC-AUC: {auc:.3f}")
    print(f"  3-fold CV ROC-AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    print(f"  Confusion matrix:\n{confusion_matrix(y_test, preds)}")
    return {'name': name, 'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1, 'roc_auc': auc,
            'cv_roc_auc_mean': cv_scores.mean(), 'pipeline': pipeline}


print("\n"+"="*80); print("MODEL COMPARISON"); print("="*80)

results = []
results.append(evaluate(
    "Logistic Regression (baseline, class_weight=balanced)",
    Pipeline([('prep', preprocessor), ('model', LogisticRegression(class_weight='balanced', max_iter=1000))])
))
results.append(evaluate(
    "Random Forest (class_weight=balanced)",
    Pipeline([('prep', preprocessor), ('model', RandomForestClassifier(n_estimators=200, max_depth=10, class_weight='balanced', random_state=42, n_jobs=-1))])
))
results.append(evaluate(
    "XGBoost (scale_pos_weight)",
    Pipeline([('prep', preprocessor), ('model', xgb.XGBClassifier(n_estimators=200, max_depth=5, scale_pos_weight=scale_pos_weight, random_state=42, n_jobs=-1, eval_metric='logloss'))])
))

print("\n"+"="*80); print("MODEL COMPARISON SUMMARY"); print("="*80)
summary = pd.DataFrame([{k: v for k, v in r.items() if k != 'pipeline'} for r in results])
print(summary.to_string(index=False))

best = max(results, key=lambda r: r['roc_auc'])
print(f"\nBest model by test ROC-AUC: {best['name']}")

best_pipeline = best['pipeline']
feature_names = (best_pipeline.named_steps['prep'].named_transformers_['cat'].get_feature_names_out(FEATURE_COLS_CATEGORICAL).tolist()
                  + FEATURE_COLS_NUMERIC)
if hasattr(best_pipeline.named_steps['model'], 'feature_importances_'):
    importances = best_pipeline.named_steps['model'].feature_importances_
    imp_df = pd.DataFrame({'feature': feature_names, 'importance': importances}).sort_values('importance', ascending=False)
    print("\nTop 15 feature importances (best model):")
    print(imp_df.head(15).to_string(index=False))
    imp_df.to_csv(WH + 'classification_feature_importance.csv', index=False)

print("\nFull classification report (best model):")
print(classification_report(y_test, best_pipeline.predict(X_test)))

joblib.dump(best_pipeline, WH + 'classification_model.pkl')
X_test.to_csv(WH + 'classification_X_test.csv', index=False,encoding="utf-8")
y_test.to_csv(WH + 'classification_y_test.csv', index=False,encoding="utf-8")
summary.to_csv(WH + 'classification_model_comparison.csv', index=False,encoding="utf-8")
print("\nSaved model, test set, and importance table.")
