"""
ML prediction utilities. Loads the trained regression/classification
pipelines (same .pkl files produced by src/ml/) and wraps them in
simple, validated predict functions the UI can call directly.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import MODEL_FILES
from utils.logger import get_logger

log = get_logger("ml_predictor")

FEATURE_COLS_NUMERIC = [
    "funding_rounds", "years_since_founded", "is_multi_round",
    "num_round_types_used", "has_debt_financing", "category_count",
]
FEATURE_COLS_CATEGORICAL = ["industry_grouped", "country_grouped"]


@st.cache_resource(show_spinner=False)
def load_models():
    import joblib
    if not MODEL_FILES["regression"].exists() or not MODEL_FILES["classification"].exists():
        raise FileNotFoundError("Model files not found in models/")
    reg = joblib.load(MODEL_FILES["regression"])
    clf = joblib.load(MODEL_FILES["classification"])
    log.info("Loaded regression and classification models.")
    return reg, clf


def build_input_row(
    funding_rounds: int, years_since_founded: float, is_multi_round: bool,
    num_round_types_used: int, has_debt_financing: bool, category_count: int,
    industry: str, country: str,
) -> pd.DataFrame:
    return pd.DataFrame([{
        "funding_rounds": funding_rounds,
        "years_since_founded": years_since_founded,
        "is_multi_round": int(is_multi_round),
        "num_round_types_used": num_round_types_used,
        "has_debt_financing": int(has_debt_financing),
        "category_count": category_count,
        "industry_grouped": industry,
        "country_grouped": country,
    }])


def predict_funding(row: pd.DataFrame) -> dict:
    reg, _ = load_models()
    log_pred = reg.predict(row)[0]
    funding = float(np.expm1(log_pred))
    return {"predicted_funding": funding, "log_prediction": float(log_pred)}


def predict_success(row: pd.DataFrame) -> dict:
    _, clf = load_models()
    proba = clf.predict_proba(row)[0]
    return {"exit_probability": float(proba[1]), "no_exit_probability": float(proba[0])}


def success_tier(probability: float) -> tuple:
    """Returns (label, color_class) for a probability."""
    if probability >= 0.5:
        return "High likelihood", "success"
    if probability >= 0.25:
        return "Moderate likelihood", "warning"
    return "Lower likelihood", "danger"
