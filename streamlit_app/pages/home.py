"""Home / Landing page."""
from components.footer import render_footer
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from components.kpi_card import kpi_row, skeleton_row
from config.settings import APP_TAGLINE, DATA_SCOPE_NOTE
from utils.data_loader import load_csv, load_denormalized_startups
from utils.error_handler import safe_run


def _fmt_money(x: float) -> str:
    if x >= 1e9:
        return f"${x/1e9:.1f}B"
    if x >= 1e6:
        return f"${x/1e6:.1f}M"
    if x >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


@safe_run("Couldn't load the headline metrics.")
def render_hero_and_kpis():
    st.markdown(
        f"""
        <div style="padding: 1.6rem 0 0.4rem 0;">
            <div class="pill pill-live" style="margin-bottom: 0.9rem;">
                <span class="pill-dot"></span> Live data · PostgreSQL-backed star schema
            </div>
            <div class="hero-title">Startup Funding Intelligence</div>
            <div class="hero-sub">{APP_TAGLINE} An end-to-end analytics platform spanning data engineering,
            statistics, machine learning, and business intelligence — built on real, sourced startup funding data.</div>
        </div>
        """,
        unsafe_allow_html=True,
        
    )
    st.caption("Developed by Md Imamuddin")

    st.markdown("<div style='height:1.3rem'></div>", unsafe_allow_html=True)

    placeholder = st.empty()
    with placeholder.container():
        skeleton_row(6)

    df = load_denormalized_startups()

    total_funding = df["funding_total_usd"].sum()
    total_startups = len(df)
    total_unicorns = int(df["is_unicorn"].sum())
    exit_rate = df["is_exited"].mean()
    median_funding = df["funding_total_usd"].median()
    countries = df["country_code"].nunique()

    placeholder.empty()
    kpi_row([
        {"label": "Total Funding", "value": _fmt_money(total_funding), "delta": "1995 – 2015 disclosed capital",
         "gradient": 1, "icon_name": "trending-up"},
        {"label": "Total Startups", "value": f"{total_startups:,}", "delta": f"across {countries} countries",
         "gradient": 2, "icon_name": "users"},
        {"label": "Unicorns Matched", "value": f"{total_unicorns}", "delta": "name + country matched",
         "gradient": 3, "icon_name": "zap"},
        {"label": "Median Funding", "value": _fmt_money(median_funding), "delta": "typical raise, not skewed by outliers",
         "gradient": 5, "icon_name": "target"},
        {"label": "Exit Rate", "value": f"{exit_rate*100:.1f}%", "delta": "IPO + acquired",
         "gradient": 4, "icon_name": "check-circle"},
        {"label": "Countries", "value": f"{countries}", "delta": "global coverage",
         "gradient": 6, "icon_name": "globe"},
    ])

    return df


@safe_run("Couldn't render the funding trend chart.")
def render_trend_chart(df: pd.DataFrame):
    date_dim = load_csv("date")
    df2 = df.copy()
    df2["first_funding_date_id"] = df2["first_funding_date_id"]
    merged = df2.merge(
        date_dim[["date_id", "year"]], left_on="first_funding_date_id", right_on="date_id", how="left"
    )
    yearly = (
        merged[merged["year"].between(1998, 2015)]
        .groupby("year")
        .agg(total_funding=("funding_total_usd", "sum"), deals=("startup_id", "count"))
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yearly["year"], y=yearly["total_funding"], name="Total Funding",
        marker=dict(color="#6366F1"), yaxis="y1",
        hovertemplate="Year %{x}<br>Funding: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=yearly["year"], y=yearly["deals"], name="Deal Count", mode="lines+markers",
        line=dict(color="#EC4899", width=3), marker=dict(size=6), yaxis="y2",
        hovertemplate="Year %{x}<br>Deals: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        title="Funding Volume vs. Deal Count by Year",
        template="plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Total Funding (USD)"),
        yaxis2=dict(title="Deal Count", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=10, r=10),
        height=380,
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't render the industry chart.")
def render_industry_chart(df: pd.DataFrame):
    ind = (
        df.groupby("primary_category")
        .agg(startups=("startup_id", "count"), total_funding=("funding_total_usd", "sum"))
        .query("startups >= 30")
        .sort_values("total_funding", ascending=False)
        .head(10)
        .sort_values("total_funding")
    )
    fig = go.Figure(go.Bar(
        x=ind["total_funding"], y=ind.index, orientation="h",
        marker=dict(
            color=ind["total_funding"], colorscale=[[0, "#C7D2FE"], [1, "#4F46E5"]], showscale=False,
        ),
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title="Top 10 Industries by Total Funding",
        template="plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=30, l=10, r=10),
        height=380,
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_nav_grid():
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    st.markdown("### Explore the platform")
    st.markdown('<p class="subtle">Every section below is built on the same validated data pipeline.</p>', unsafe_allow_html=True)

    cards = [
        {"icon": "chart-bar", "title": "Exploratory Analysis", "desc": "101 insights across funding trends, industries, and geography.", "grad": 1},
        {"icon": "flask", "title": "Statistical Analysis", "desc": "Hypothesis tests, confidence intervals, regression diagnostics.", "grad": 2},
        {"icon": "database", "title": "SQL Insights", "desc": "Window functions, CTEs, and materialized-view performance benchmarks.", "grad": 5},
        {"icon": "brain", "title": "ML Predictions", "desc": "Live funding and success prediction, backed by tuned models.", "grad": 3},
        {"icon": "layers", "title": "SHAP Explainability", "desc": "See exactly why the models predict what they predict.", "grad": 4},
        {"icon": "compass", "title": "Explorer", "desc": "Search startups, investors, countries, and industries directly.", "grad": 6},
        {"icon": "sitemap", "title": "Architecture", "desc": "The full data engineering → BI pipeline, end to end.", "grad": 2},
        {"icon": "book", "title": "Documentation", "desc": "Data dictionary, glossary, and methodology reports.", "grad": 5},
    ]

    cols = st.columns(4)
    for i, c in enumerate(cards):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="app-card" style="margin-bottom: 1rem; min-height: 148px;">
                    <div style="width:36px; height:36px; border-radius:9px; background: var(--kpi-grad-{c['grad']}, var(--surface-hover));
                                display:flex; align-items:center; justify-content:center; margin-bottom:0.7rem;
                                background: linear-gradient(135deg, var(--accent-1), var(--accent-2));">
                        {icon(c['icon'], size=17, color='#FFFFFF')}
                    </div>
                    <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">{c['title']}</div>
                    <div class="subtle" style="font-size:0.82rem; line-height:1.4;">{c['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_scope_footer():
    st.markdown(
        f"""
        <div class="app-card" style="margin-top: 0.5rem; display:flex; align-items:flex-start; gap:0.7rem;">
            {icon('info', size=18)}
            <div>
                <strong style="font-size:0.88rem;">Data scope</strong>
                <p class="subtle" style="margin: 0.2rem 0 0 0; font-size:0.85rem;">{DATA_SCOPE_NOTE}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render():
    df = render_hero_and_kpis()
    if df is None:
        return

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        render_trend_chart(df)
    with col2:
        render_industry_chart(df)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_nav_grid()

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    render_scope_footer()
    render_footer()
