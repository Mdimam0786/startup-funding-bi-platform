"""About page: project credits, tech highlights, and contact links."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from config.settings import APP_NAME, APP_VERSION, GITHUB_URL, LINKEDIN_URL, RESUME_PATH


def render_header():
    st.markdown(
        f"""
        <div class="hero-title" style="font-size:2.1rem;">About This Project</div>
        <p class="hero-sub">{APP_NAME} · v{APP_VERSION} — a full-stack analytics platform I built to
        cover the complete data-to-decision lifecycle on real, sourced startup funding data.</p>
        <p class="subtle" style="font-size:0.85rem; margin-top:-0.4rem;">Made by Md Imamuddin</p>
        """,
        unsafe_allow_html=True,
    )


def render_summary_cards():
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    cards = [
        {"icon": "database", "title": "Data Engineering", "desc": "3 real datasets, cleaned and merged into a validated PostgreSQL star schema.", "grad": 1},
        {"icon": "flask", "title": "Statistics", "desc": "Hypothesis tests and regression diagnostics with assumptions actually checked.", "grad": 2},
        {"icon": "brain", "title": "Machine Learning", "desc": "3 model use cases, cross-validated and SHAP-explained.", "grad": 3},
        {"icon": "chart-bar", "title": "Business Intelligence", "desc": "43-measure Power BI dashboard + this Streamlit showcase.", "grad": 5},
    ]
    cols = st.columns(4)
    for col, c in zip(cols, cards):
        with col:
            st.markdown(
                f"""<div class="app-card" style="min-height:150px;">
                <div style="width:32px; height:32px; border-radius:8px; margin-bottom:0.6rem;
                            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
                            display:flex; align-items:center; justify-content:center;">
                    {icon(c['icon'], size=16, color='#FFFFFF')}
                </div>
                <div style="font-weight:700; font-size:0.9rem;">{c['title']}</div>
                <div class="subtle" style="font-size:0.78rem; margin-top:0.3rem; line-height:1.4;">{c['desc']}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_build_notes():
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    st.markdown("### How this was built")
    st.markdown(
        """
        <div class="app-card">
        <p class="subtle" style="font-size:0.87rem; line-height:1.7;">
        Every part of this project — from the initial data cleaning through the final Streamlit page —
        has a working script or app behind it, not just a written description. I've documented the bugs I ran
        into along the way (a category-parsing error that silently caused 77% false-missingness, a join fan-out
        that duplicated fact rows, a sparse-vs-dense XGBoost prediction mismatch in the SHAP explainer) instead
        of hiding them, because that's closer to how real analytics engineering actually goes. The
        <a href="#" onclick="return false;">Documentation</a> page in the sidebar has the full methodology behind
        every number on this site.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_contact():
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    st.markdown("### Get in touch")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<a href="{GITHUB_URL}" target="_blank" style="text-decoration:none;">
            <div class="app-card" style="text-align:center;">
                {icon('github', size=22)}
                <div style="font-weight:700; font-size:0.88rem; margin-top:0.5rem;">GitHub</div>
                <div class="subtle" style="font-size:0.76rem;">Full source code</div>
            </div></a>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<a href="{LINKEDIN_URL}" target="_blank" style="text-decoration:none;">
            <div class="app-card" style="text-align:center;">
                {icon('linkedin', size=22)}
                <div style="font-weight:700; font-size:0.88rem; margin-top:0.5rem;">LinkedIn</div>
                <div class="subtle" style="font-size:0.76rem;">Let\'s connect</div>
            </div></a>""",
            unsafe_allow_html=True,
        )
    with c3:
        if RESUME_PATH.exists():
            with open(RESUME_PATH, "rb") as f:
                st.download_button("📄  Download Résumé", data=f, file_name="resume.pdf",
                                    mime="application/pdf", width="stretch")
        else:
            st.markdown(
                """<div class="app-card" style="text-align:center;">
                <div style="font-size:1.4rem;">📄</div>
                <div style="font-weight:700; font-size:0.88rem; margin-top:0.5rem;">Résumé</div>
                <div class="subtle" style="font-size:0.76rem;">Not uploaded yet</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render():
    render_header()
    render_summary_cards()
    render_build_notes()
    render_contact()