"""
Main entry point. Run with: streamlit run app.py

Architecture: this file owns page config, theme CSS injection, sidebar
chrome, and st.navigation wiring. Each page's actual content lives in
pages/*.py as a render() function, imported and passed to st.Page as a
callable -- keeps everything in one process, testable, and avoids the
older file-path-based multipage pattern's styling limitations.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))

from config.theme import build_css
from components.sidebar import render_sidebar_header, render_theme_toggle, render_sidebar_footer
from utils.logger import get_logger

log = get_logger("app")

st.set_page_config(
    page_title="Startup Funding Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Session state defaults ----------------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

# ---------------- Theme CSS (must inject before any content renders) ----------------
st.markdown(build_css(st.session_state.theme_mode), unsafe_allow_html=True)

# ---------------- Pages ----------------
from pages import home as home_page  # noqa: E402
from pages import eda as eda_page  # noqa: E402
from pages import statistics as statistics_page  # noqa: E402
from pages import sql_insights as sql_insights_page  # noqa: E402
from pages import ml_predictions as ml_predictions_page  # noqa: E402
from pages import shap_explainability as shap_page  # noqa: E402
from pages import explorer as explorer_page  # noqa: E402
from pages import architecture as architecture_page  # noqa: E402
from pages import documentation as documentation_page  # noqa: E402
from pages import about as about_page  # noqa: E402

home = st.Page(home_page.render, title="Home", icon="🏠", url_path="home", default=True)
eda = st.Page(eda_page.render, title="EDA", icon="📈", url_path="eda")
statistics = st.Page(statistics_page.render, title="Statistics", icon="🧪", url_path="statistics")
sql_insights = st.Page(sql_insights_page.render, title="SQL Insights", icon="🗄️", url_path="sql-insights")
ml_predictions = st.Page(ml_predictions_page.render, title="ML Predictions", icon="🤖", url_path="ml-predictions")
shap_explainability = st.Page(shap_page.render, title="SHAP Explainability", icon="🔍", url_path="shap")
explorer = st.Page(explorer_page.render, title="Explorer", icon="🧭", url_path="explorer")
architecture = st.Page(architecture_page.render, title="Architecture", icon="🏗️", url_path="architecture")
documentation = st.Page(documentation_page.render, title="Documentation", icon="📚", url_path="documentation")
about = st.Page(about_page.render, title="About", icon="👤", url_path="about")

pages = {
    "Overview": [home],
    "Analysis": [eda, statistics, sql_insights],
    "Machine Learning": [ml_predictions, shap_explainability],
    "Explore": [explorer],
    "Project": [architecture, documentation, about],
}

# ---------------- Sidebar ----------------
with st.sidebar:
    render_sidebar_header()
    nav = st.navigation(pages, position="sidebar")
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    render_theme_toggle()
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    render_sidebar_footer()

# ---------------- Run selected page ----------------
try:
    nav.run()
except Exception as e:
    log.error(f"Page render failed: {e}")
    st.error(f"This page hit an unexpected error: {e}")
