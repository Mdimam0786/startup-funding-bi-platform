"""Architecture page: the full data engineering -> BI pipeline, visualized
as an interactive Sankey flow, plus a live self-diagnostic panel checking
which parts of the stack are actually reachable right now."""
import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from config.settings import DATA_DIR, MODELS_DIR, FILES, MODEL_FILES
from utils.db_connector import is_live
from utils.error_handler import safe_run


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def render_header():
    st.markdown(
        """
        <div class="pill pill-live"><span class="pill-dot"></span> Every stage shown below is implemented in this project.</div>
        <div style="height:0.5rem"></div>
        <h1 style="margin-bottom:0.1rem;">Architecture</h1>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Developed by Md Imamuddin")

    st.markdown(
        """
        <p class="subtle" style="margin-top:0;">
        From raw startup datasets to an interactive analytics platform,
        covering the complete data engineering, machine learning,
        and business intelligence workflow.
        </p>
        """,
        unsafe_allow_html=True,
    )

@safe_run("Couldn't render the pipeline flow diagram.")
def render_sankey():
    st.markdown("### Data Flow")

    labels = [
        "Crunchbase Funding\n(54,294 rows)", "Success/Fail Status\n(66,368 rows)", "Unicorn List\n(1,359 rows)",  # 0,1,2
        "Cleaning & Validation", "Merged Fact Table\n(67,098 startups)",  # 3,4
        "PostgreSQL Star Schema",  # 5
        "SQL Analytics Layer", "EDA & Statistics", "ML Models",  # 6,7,8
        "Power BI Dashboard", "Streamlit App",  # 9,10
    ]
    colors = ["#6366F1", "#6366F1", "#6366F1", "#8B5CF6", "#8B5CF6", "#EC4899",
              "#F59E0B", "#F59E0B", "#F59E0B", "#10B981", "#10B981"]

    source = [0, 1, 2, 3, 4, 5, 5, 5, 6, 7, 8, 6, 7, 8]
    target = [3, 3, 3, 4, 5, 6, 7, 8, 9, 9, 9, 10, 10, 10]
    value = [54, 66, 1.4, 121, 67, 67, 67, 67, 22, 22, 23, 22, 22, 23]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=18, thickness=18, line=dict(color="rgba(0,0,0,0)", width=0),
            label=labels, color=colors,
        ),
        link=dict(source=source, target=target, value=value,
                   color="rgba(99,102,241,0.25)"),
    ))
    fig.update_layout(
        template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=10, r=10), height=440,
        font=dict(size=11),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown('<p class="subtle" style="font-size:0.78rem;">Flow widths are illustrative (row counts in thousands), not perfectly to scale.</p>', unsafe_allow_html=True)


@safe_run("Couldn't render the live diagnostics panel.")
def render_diagnostics():
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("### Live System Status")
    st.markdown('<p class="subtle">Checked right now, not cached documentation.</p>', unsafe_allow_html=True)

    checks = []

    db_live = is_live()
    checks.append(("PostgreSQL Connection", db_live, "Live query execution available" if db_live else "Using pandas fallback (see SQL Insights)"))

    data_ok = all(f.exists() for f in FILES.values())
    checks.append(("Warehouse Data Files", data_ok, f"{sum(1 for f in FILES.values() if f.exists())}/{len(FILES)} files found"))

    models_ok = all(f.exists() for f in MODEL_FILES.values())
    checks.append(("ML Model Files", models_ok, f"{sum(1 for f in MODEL_FILES.values() if f.exists())}/{len(MODEL_FILES)} models found"))

    cols = st.columns(3)
    for col, (label, ok, detail) in zip(cols, checks):
        with col:
            pill_class = "pill-live" if ok else "pill-warn"
            status_text = "Online" if ok else "Degraded"
            st.markdown(
                f"""<div class="app-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:0.85rem;">{label}</strong>
                    <span class="pill {pill_class}"><span class="pill-dot"></span>{status_text}</span>
                </div>
                <p class="subtle" style="font-size:0.78rem; margin-top:0.5rem;">{detail}</p>
                </div>""",
                unsafe_allow_html=True,
            )


def render_tech_stack():
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    st.markdown("### Tech Stack")

    stack = [
        {"name": "Python 3.12", "role": "Data engineering, ML, app logic", "icon": "zap", "grad": 1},
        {"name": "PostgreSQL 16", "role": "Star schema, SQL analytics layer", "icon": "database", "grad": 5},
        {"name": "scikit-learn / XGBoost", "role": "Regression, classification, clustering", "icon": "brain", "grad": 3},
        {"name": "SHAP", "role": "Model explainability", "icon": "layers", "grad": 2},
        {"name": "Power BI", "role": "Executive dashboard, DAX, 43 measures", "icon": "chart-bar", "grad": 6},
        {"name": "Streamlit", "role": "This app — the online showcase", "icon": "compass", "grad": 4},
    ]
    cols = st.columns(3)
    for i, s in enumerate(stack):
        with cols[i % 3]:
            st.markdown(
                f"""<div class="app-card" style="margin-bottom:1rem; min-height:110px;">
                <div style="width:32px; height:32px; border-radius:8px; margin-bottom:0.6rem;
                            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
                            display:flex; align-items:center; justify-content:center;">
                    {icon(s['icon'], size=16, color='#FFFFFF')}
                </div>
                <div style="font-weight:700; font-size:0.88rem;">{s['name']}</div>
                <div class="subtle" style="font-size:0.78rem; margin-top:0.2rem;">{s['role']}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_star_schema():
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("### Star Schema")
    st.markdown('<p class="subtle">Two deliberately different fact-table grains — see the Documentation page for the full reasoning.</p>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="app-card mono" style="font-size:0.78rem; line-height:1.7; overflow-x:auto; white-space:pre;">
                         dim_date (role-playing x3)
                                  │
    dim_geography ◄────── fact_startup_funding ──────► dim_industry
                              │         │
                        startup_id      │
                              │         │
                        dim_startup     │
                              │         │
                              └────► fact_funding_by_type ◄──── dim_round_type
                                    (unpivoted, grain = startup × round type)
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_folder_structure():
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    with st.expander("📁 Full project folder structure"):
        st.code("""
startup-funding-bi-platform/
├── data/{raw,interim,processed,warehouse}/
├── src/
│   ├── data_engineering/    # extract, clean, transform, validate
│   ├── database/            # schema.sql, etl_load.py, queries/
│   ├── eda/                 # compute_eda_stats.py, generate_charts.py
│   ├── stats/                # statistical_analysis.py, diagnostics
│   ├── ml/                  # regression, classification, clustering, SHAP
│   └── utils/                # logger
├── powerbi/                 # dax_measures.dax, dashboard_specification.md
├── streamlit_app/            # this application
│   ├── app.py
│   ├── config/               # settings, theme
│   ├── pages/                 # one render() function per page
│   ├── components/            # icons, kpi_card, sidebar
│   ├── utils/                 # data_loader, db_connector, ml_predictor, shap_engine
│   ├── data/                  # copied warehouse CSVs
│   └── models/                 # copied .pkl models
├── docs/                     # all written reports
├── config/config.yaml
└── requirements.txt
        """, language="text")


def render():
    render_header()
    render_sankey()
    render_diagnostics()
    render_tech_stack()
    render_star_schema()
    render_folder_structure()
