"""SHAP Explainability page: global feature importance for the regression
and classification models, computed from the full training set."""
from components.footer import render_footer
import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.data_loader import load_csv
from utils.error_handler import safe_run


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def render_header():
    st.markdown(
        """
        <div class="pill pill-live"><span class="pill-dot"></span> SHAP TreeExplainer · computed on the full training set</div>
        <div style="height:0.5rem"></div>
        <h1 style="margin-bottom:0.1rem;">SHAP Explainability</h1>
        <p class="subtle" style="margin-top:0;">Which features actually drive each model's predictions,
        ranked by average impact across the training data — not just raw feature importance from the model itself.</p>
        """,
        unsafe_allow_html=True,
    )
  


@safe_run("Couldn't render the global feature importance section.")
def section_global_importance():
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        reg_imp = load_csv("regression_importance").sort_values("importance", ascending=False).head(10).sort_values("importance")
        fig = go.Figure(go.Bar(x=reg_imp["importance"], y=reg_imp["feature"], orientation="h",
                                marker_color="#0CA678"))
        fig.update_layout(title="Regression: Top 10 Features", template=_theme_template(),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=50, b=30, l=10, r=10), height=380)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with col2:
        clf_imp = load_csv("classification_importance").sort_values("importance", ascending=False).head(10).sort_values("importance")
        fig2 = go.Figure(go.Bar(x=clf_imp["importance"], y=clf_imp["feature"], orientation="h",
                                 marker_color="#E64980"))
        fig2.update_layout(title="Classification: Top 10 Features", template=_theme_template(),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            margin=dict(t=50, b=30, l=10, r=10), height=380)
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})


def render():
    render_header()
    section_global_importance()
    render_footer()