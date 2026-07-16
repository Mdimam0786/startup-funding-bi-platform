"""SQL Insights page: runs the project's actual window-function queries
live against PostgreSQL when available, falling back to an equivalent
pandas computation (clearly labeled) when it isn't -- e.g. when this app
is deployed somewhere without DB access."""
from components.footer import render_footer
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from utils.data_loader import load_csv, load_denormalized_startups
from utils.db_connector import is_live, run_query, explain_analyze_timing
from utils.error_handler import safe_run
from utils.sql_queries import (
    QUERIES, fallback_top_funded_per_industry, fallback_yoy_growth,
    fallback_country_pareto, fallback_funding_decile,
)

FALLBACKS = {
    "top_funded_per_industry": lambda df, date_dim: fallback_top_funded_per_industry(df),
    "yoy_growth": lambda df, date_dim: fallback_yoy_growth(df, date_dim),
    "country_pareto": lambda df, date_dim: fallback_country_pareto(df),
    "funding_decile": lambda df, date_dim: fallback_funding_decile(df),
}


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def render_header():
    live = is_live()
    status_html = (
        '<div class="pill pill-live"><span class="pill-dot"></span> Live PostgreSQL connection</div>'
        if live else
        '<div class="pill pill-static"><span class="pill-dot"></span> No live DB connection — showing pandas-equivalent results computed from the same data</div>'
    )
    st.markdown(
        f"""
        {status_html}
        <div style="height:0.5rem"></div>
        <h1 style="margin-bottom:0.1rem;">SQL Insights</h1>
        <p class="subtle" style="margin-top:0;">Window functions, CTEs, and materialized-view performance —
        the actual queries from the project's PostgreSQL analytics layer, not a simplified rewrite.</p>
        """,
        unsafe_allow_html=True,
    )
    


@safe_run("Couldn't run the query library section.")
def section_query_library(df: pd.DataFrame, date_dim: pd.DataFrame):
    st.markdown("### Query Library")
    query_key = st.selectbox(
        "Choose a query", options=list(QUERIES.keys()),
        format_func=lambda k: QUERIES[k]["label"],
    )
    query = QUERIES[query_key]
    st.markdown(f'<p class="subtle" style="font-size:0.85rem;">{query["description"]}</p>', unsafe_allow_html=True)

    st.code(query["sql"], language="sql")

    live = is_live()
    if live:
        try:
            result_df = run_query(query["sql"])
            source_label = "Live PostgreSQL"
        except Exception:
            result_df = FALLBACKS[query_key](df, date_dim)
            source_label = "Pandas fallback (query failed)"
    else:
        result_df = FALLBACKS[query_key](df, date_dim)
        source_label = "Pandas fallback (no DB connection)"

    st.markdown(f'<p class="subtle" style="font-size:0.78rem;">Result source: <strong>{source_label}</strong> · {len(result_df):,} rows</p>', unsafe_allow_html=True)

    gb = GridOptionsBuilder.from_dataframe(result_df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_default_column(sortable=True, filter=True, resizable=True)
    AgGrid(
        result_df, gridOptions=gb.build(), height=380,
        theme="alpine-dark" if st.session_state.get("theme_mode") == "dark" else "alpine",
        fit_columns_on_grid_load=True,
    )

    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download result (CSV)", data=csv, file_name=f"{query_key}.csv", mime="text/csv")

    # A quick visual for the two queries where it adds real value
    if query_key == "yoy_growth":
        fig = go.Figure()
        fig.add_trace(go.Bar(x=result_df["year"], y=result_df["total_funding"], marker_color="#6366F1", name="Total Funding"))
        fig.add_trace(go.Scatter(x=result_df["year"], y=result_df["yoy_growth_pct"], mode="lines+markers",
                                  line=dict(color="#EC4899", width=2), yaxis="y2", name="YoY Growth %"))
        fig.update_layout(template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(title="Total Funding"), yaxis2=dict(title="YoY %", overlaying="y", side="right"),
                           margin=dict(t=20, b=30, l=10, r=10), height=320, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    elif query_key == "country_pareto":
        fig = px.area(result_df.head(20), x="country_rank", y="cumulative_pct_of_global_funding",
                       title="Cumulative % of Global Funding by Country Rank", template=_theme_template())
        fig.update_traces(line_color="#8B5CF6", fillcolor="rgba(139,92,246,0.2)")
        fig.add_hline(y=80, line_dash="dash", line_color="#EF4444", annotation_text="80% threshold")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=50, b=30, l=10, r=10), height=320)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't render the materialized view benchmark section.")
def section_mv_benchmark():
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("### Materialized View Performance")
    st.markdown('<p class="subtle">Benchmarked with EXPLAIN ANALYZE — the actual reason the project\'s materialized views exist.</p>', unsafe_allow_html=True)

    live_query = """SELECT i.primary_category, SUM(f.funding_total_usd)
FROM startup_bi.fact_startup_funding f
JOIN startup_bi.dim_industry i ON f.industry_id = i.industry_id
GROUP BY i.primary_category;"""
    mv_query = "SELECT primary_category, total_funding FROM startup_bi.mv_industry_summary;"

    if is_live():
        try:
            live_ms = explain_analyze_timing(live_query)
            mv_ms = explain_analyze_timing(mv_query)
            source = "Measured live, this session"
        except Exception:
            live_ms, mv_ms, source = 32.874, 0.127, "Cached benchmark from project documentation (live measurement failed)"
    else:
        live_ms, mv_ms, source = 32.874, 0.127, "Cached benchmark from project documentation (no live DB connection)"

    speedup = live_ms / mv_ms if mv_ms > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Live aggregation query", f"{live_ms:.2f} ms")
    c2.metric("Materialized view query", f"{mv_ms:.3f} ms")
    c3.metric("Speedup", f"{speedup:.0f}x")
    st.markdown(f'<p class="subtle" style="font-size:0.78rem;">{source}</p>', unsafe_allow_html=True)

    fig = go.Figure(go.Bar(
        x=["Live Aggregation", "Materialized View"], y=[live_ms, mv_ms],
        marker_color=["#8B92A8", "#10B981"], text=[f"{live_ms:.2f} ms", f"{mv_ms:.3f} ms"], textposition="outside",
    ))
    fig.update_layout(template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       yaxis_title="Execution time (ms, log scale)", yaxis_type="log",
                       margin=dict(t=20, b=30, l=10, r=10), height=320)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with st.expander("Why this speedup exists"):
        st.markdown("""
        The live query aggregates all 67,098 rows of `fact_startup_funding` on every call.
        `mv_industry_summary` pre-computes that aggregation once and stores it physically —
        querying it is just reading ~800 pre-computed rows. The trade-off: materialized views
        need an explicit `REFRESH` after new data loads (see `refresh_materialized_views()` in
        the project's SQL layer), so they're a deliberate freshness-vs-speed choice, not a free lunch.
        """)


def render():
    render_header()
    df = load_denormalized_startups()
    date_dim = load_csv("date")

    section_query_library(df, date_dim)
    section_mv_benchmark()

    st.markdown(
        f"""<div class="app-card" style="margin-top:1rem; display:flex; align-items:flex-start; gap:0.7rem;">
        {icon('info', size=18)}
        <div><strong style="font-size:0.88rem;">About the fallback design</strong>
        <p class="subtle" style="margin:0.2rem 0 0 0; font-size:0.85rem;">This page tries a live PostgreSQL
        connection first (via <code>st.secrets</code> or environment variables) and transparently falls back
        to an equivalent pandas computation on the same underlying data if no database is reachable — so the
        page works whether this app is running next to the project's database or deployed standalone.</p></div></div>""",
        unsafe_allow_html=True,
    )
    render_footer()
