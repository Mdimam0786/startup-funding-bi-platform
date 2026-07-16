"""
SHAP explainability engine. Builds TreeExplainers for the trained
regression/classification models and computes per-instance SHAP values
for whatever input row the user is currently exploring (shared via
st.session_state with the ML Predictions page).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.logger import get_logger
from utils.ml_predictor import load_models, FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL

log = get_logger("shap_engine")


def _to_float(x):
    """Coerce a value that may be a numpy scalar, nested list/array, sparse
    matrix row, or (a known shap/xgboost version-mismatch quirk) a stringified
    number like '1.4278026E1' straight from XGBoost's internal JSON config,
    into a clean Python float."""
    if hasattr(x, "toarray"):
        x = x.toarray()
    while isinstance(x, (list, tuple, np.ndarray)):
        if len(x) == 0:
            return 0.0
        x = x[0]
    if isinstance(x, str):
        x = x.strip().strip("[]").strip("'\"")
    return float(x)


def _to_float_array(values) -> np.ndarray:
    """Same idea as _to_float but for a 1D vector of SHAP values -- handles
    sparse-matrix output from TreeExplainer (a real risk here since we
    deliberately feed it a sparse input, see explain_funding_prediction)."""
    if hasattr(values, "toarray"):
        values = values.toarray()
    values = np.asarray(values)
    if values.ndim > 1:
        values = values.reshape(-1)
    if values.dtype == object or values.dtype.kind in ("U", "S"):
        values = np.array([_to_float(v) for v in values], dtype=float)
    else:
        values = values.astype(float)
    return values


def _feature_names(pipeline) -> list:
    cat_names = pipeline.named_steps["prep"].named_transformers_["cat"].get_feature_names_out(FEATURE_COLS_CATEGORICAL).tolist()
    return cat_names + FEATURE_COLS_NUMERIC


@st.cache_resource(show_spinner=False)
def get_explainers():
    import shap
    reg, clf = load_models()
    reg_explainer = shap.TreeExplainer(reg.named_steps["model"])
    clf_explainer = shap.TreeExplainer(clf.named_steps["model"])
    log.info("Built SHAP TreeExplainers for both models.")
    return reg_explainer, clf_explainer


def explain_funding_prediction(row: pd.DataFrame) -> dict:
    reg, _ = load_models()
    reg_explainer, _ = get_explainers()

    # IMPORTANT: do NOT densify this. XGBoost's DMatrix treats an implicit
    # (unstored) zero in a sparse matrix as "missing", but treats a zero in
    # a dense ndarray as a literal 0 -- two different semantics. The trained
    # pipeline's .predict() runs on the sparse output of the ColumnTransformer,
    # so SHAP must explain that exact same sparse input, or its values won't
    # reconstruct the real prediction (verified: densifying here silently
    # shifted the base+contribution sum by ~2 log-units in testing).
    transformed = reg.named_steps["prep"].transform(row)

    shap_values = reg_explainer.shap_values(transformed)
    base_value = _to_float(reg_explainer.expected_value)

    names = _feature_names(reg)
    raw_values = shap_values[0] if getattr(shap_values, "ndim", 1) > 1 else shap_values
    values = _to_float_array(raw_values)

    return {
        "feature_names": names,
        "shap_values": values,
        "base_value": base_value,
        "feature_values": np.asarray(transformed.todense())[0] if hasattr(transformed, "todense") else transformed[0],
    }


def explain_success_prediction(row: pd.DataFrame) -> dict:
    _, clf = load_models()
    _, clf_explainer = get_explainers()

    transformed = clf.named_steps["prep"].transform(row)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    transformed = np.asarray(transformed, dtype=float)

    shap_values = clf_explainer.shap_values(transformed)
    base_value = clf_explainer.expected_value

    # Random Forest classifier: shap_values may come back as a list [class0, class1]
    # or a 3D array (n, features, n_classes) depending on the shap/sklearn version.
    if isinstance(shap_values, list):
        raw_values = shap_values[1][0]
    elif getattr(shap_values, "ndim", 1) == 3:
        raw_values = shap_values[0, :, 1]
    else:
        raw_values = shap_values[0]
    values = _to_float_array(raw_values)

    if isinstance(base_value, (list, np.ndarray)):
        base_value = _to_float(np.ravel(base_value)[-1])
    else:
        base_value = _to_float(base_value)

    names = _feature_names(clf)

    return {
        "feature_names": names,
        "shap_values": values,
        "base_value": base_value,
        "feature_values": transformed[0],
    }