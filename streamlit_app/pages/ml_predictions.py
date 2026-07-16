"""ML Predictions page: live inference against the trained regression and
classification pipelines, driven by an interactive company-profile form."""
from components.footer import render_footer
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from utils.data_loader import load_denormalized_startups
from utils.error_handler import safe_run
from utils.ml_predictor import (
    build_input_row, predict_funding, predict_success, success_tier,
    FEATURE_COLS_NUMERIC,
)

TOP_INDUSTRIES = [
    "Software", "Biotechnology", "E-Commerce", "Mobile", "Health Care", "Curated Web",
    "Clean Technology", "Advertising", "Enterprise Software", "Finance",
    "Health and Wellness", "Education", "Hardware + Software", "Games", "Apps", "Other",
]
TOP_COUNTRIES = [
    "United States", "United Kingdom", "Canada", "India", "China", "Germany", "France",
    "Israel", "Spain", "Netherlands", "Australia", "Sweden", "Singapore",
    "Russian Federation", "Brazil", "Other",
]


def _fmt_money(x: float) -> str:
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    if x >= 1e6:
        return f"${x/1e6:.2f}M"
    if x >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def render_header():
    st.markdown(
        """
        <div class="pill pill-live"><span class="pill-dot"></span> Live inference · tuned XGBoost + Random Forest pipelines</div>
        <div style="height:0.5rem"></div>
        <h1 style="margin-bottom:0.1rem;">ML Predictions</h1>
        <p class="subtle" style="margin-top:0;">Describe a startup's funding profile — get a live predicted funding
        amount and exit-likelihood score from the same models built and validated in the project's ML phase
        (R² = 0.515, ROC-AUC = 0.800).</p>
        """,
        unsafe_allow_html=True,
    )
    


@safe_run("Couldn't render the prediction form.")
def render_input_form():
    st.markdown("### Company Profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        funding_rounds = st.number_input("Funding rounds so far", min_value=1, max_value=15, value=2, step=1)
        years_since_founded = st.slider("Years since founded", 0.0, 20.0, 4.0, step=0.5)
    with c2:
        num_round_types_used = st.number_input("Distinct round types used", min_value=1, max_value=10, value=1, step=1,
                                                  help="e.g. seed + venture = 2 distinct types")
        category_count = st.number_input("Number of category tags", min_value=1, max_value=10, value=2, step=1)
    with c3:
        industry = st.selectbox("Industry", TOP_INDUSTRIES, index=0)
        country = st.selectbox("Country", TOP_COUNTRIES, index=0)

    c4, c5 = st.columns(2)
    with c4:
        is_multi_round = st.toggle("Has raised more than one round", value=(funding_rounds > 1))
    with c5:
        has_debt_financing = st.toggle("Has used debt financing", value=False)

    row = build_input_row(
        funding_rounds=funding_rounds, years_since_founded=years_since_founded,
        is_multi_round=is_multi_round, num_round_types_used=num_round_types_used,
        has_debt_financing=has_debt_financing, category_count=category_count,
        industry=industry, country=country,
    )
    return row


@safe_run("Couldn't run the funding prediction.")
def render_funding_prediction(row: pd.DataFrame, df: pd.DataFrame):
    result = predict_funding(row)
    predicted = result["predicted_funding"]

    all_funding = df["funding_total_usd"].dropna()
    percentile = (all_funding < predicted).mean() * 100

    st.markdown(
        f"""
        <div class="kpi-card kpi-grad-1" style="min-height:150px;">
            <div class="kpi-label">Predicted Total Funding</div>
            <div class="kpi-value" style="font-size:2.1rem;">{_fmt_money(predicted)}</div>
            <div class="kpi-delta">≈ {percentile:.0f}th percentile of all tracked startups</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=np.log1p(all_funding), nbinsx=60, marker_color="#232838", name="All startups"))
    fig.add_vline(x=np.log1p(predicted), line_color="#EC4899", line_width=3,
                   annotation_text="Your input", annotation_position="top")
    fig.update_layout(
        title="Where this prediction sits in the overall funding distribution",
        template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="log(1 + Funding USD)", yaxis_title="Startup count",
        margin=dict(t=50, b=30, l=10, r=10), height=280, showlegend=False,
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't run the success prediction.")
def render_success_prediction(row: pd.DataFrame):
    result = predict_success(row)
    prob = result["exit_probability"]
    label, color = success_tier(prob)

    gradient_map = {"success": 4, "warning": 6, "danger": 3}
    st.markdown(
        f"""
        <div class="kpi-card kpi-grad-{gradient_map[color]}" style="min-height:150px;">
            <div class="kpi-label">Predicted Exit Probability</div>
            <div class="kpi-value" style="font-size:2.1rem;">{prob*100:.1f}%</div>
            <div class="kpi-delta">{label} of reaching IPO or acquisition</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=prob * 100,
        number={"suffix": "%", "font": {"size": 26}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#5B6178"},
            "bar": {"color": "#8B5CF6"},
            "steps": [
                {"range": [0, 25], "color": "rgba(239,68,68,0.25)"},
                {"range": [25, 50], "color": "rgba(245,158,11,0.25)"},
                {"range": [50, 100], "color": "rgba(16,185,129,0.25)"},
            ],
        },
    ))
    fig.update_layout(template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)",
                       margin=dict(t=20, b=10, l=20, r=20), height=240)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_caveat():
    st.markdown(
        f"""<div class="app-card" style="margin-top:0.5rem; display:flex; align-items:flex-start; gap:0.7rem;">
        {icon('info', size=18)}
        <div><strong style="font-size:0.88rem;">Read this before trusting the exit-probability number</strong>
        <p class="subtle" style="margin:0.2rem 0 0 0; font-size:0.85rem;">
        The classification model's single strongest feature is <code>years_since_founded</code> — partly because
        older companies in this historical (2015-cutoff) dataset simply had more time to reach an exit before the
        snapshot was taken, not necessarily because age itself drives success. Read this model's output as
        <em>"given elapsed time, how likely does this profile look like an exit"</em> rather than a forward-looking
        guarantee. Full explanation on the SHAP Explainability page.</p></div></div>""",
        unsafe_allow_html=True,
    )


def render():
    render_header()
    df = load_denormalized_startups()

    row = render_input_form()
    if row is None:
        return

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        render_funding_prediction(row, df)
    with col2:
        render_success_prediction(row)

    render_caveat()
    render_footer()

