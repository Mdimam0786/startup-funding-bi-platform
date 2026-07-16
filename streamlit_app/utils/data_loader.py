"""
Cached data loading. Every CSV/model load in the app goes through here
so Streamlit's cache keeps this fast on rerun (Streamlit reruns the whole
script on every interaction, so uncached pd.read_csv calls would be a
real performance problem on a 67K-row+ dataset).
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import FILES, MODEL_FILES
from utils.logger import get_logger

log = get_logger("data_loader")


@st.cache_data(show_spinner=False, ttl=3600)
def load_csv(key: str) -> pd.DataFrame:
    path = FILES[key]
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, low_memory=False)
    log.info(f"Loaded {key}: {len(df):,} rows from {path.name}")
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def load_denormalized_startups() -> pd.DataFrame:
    """The single most-used table across the app: fact joined to its core dims."""
    fact = load_csv("fact_funding")
    startup = load_csv("startup")
    geo = load_csv("geography")
    industry = load_csv("industry")

    df = (
        fact.merge(startup, on="startup_id", how="left")
        .merge(geo, on="geography_id", how="left")
        .merge(industry, on="industry_id", how="left")
    )
    return df


@st.cache_resource(show_spinner=False)
def load_model(key: str):
    import joblib
    path = MODEL_FILES[key]
    if not path.exists():
        raise FileNotFoundError(path)
    model = joblib.load(path)
    log.info(f"Loaded model: {key}")
    return model


@st.cache_data(show_spinner=False, ttl=3600)
def get_filter_options(df: pd.DataFrame, column: str) -> list:
    return sorted(df[column].dropna().unique().tolist())
