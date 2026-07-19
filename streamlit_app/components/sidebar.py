"""
Custom sidebar: brand header, theme toggle, and footer with GitHub/LinkedIn/
resume links. Page navigation itself is handled by st.navigation in app.py
(the modern Streamlit API) -- this renders the chrome around it.
"""
import streamlit as st

from components.icons import icon
from config.settings import APP_NAME, GITHUB_URL, LINKEDIN_URL, RESUME_PATH


def render_sidebar_header():
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:0.6rem; padding: 0 0.2rem 1rem 0.2rem;
                    border-bottom: 1px solid var(--border); margin-bottom: 0.8rem;">
            <div style="width:34px; height:34px; border-radius:9px; background: var(--gradient-main);
                        display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                <span style="color:white; font-weight:800; font-size:1rem;">S</span>
            </div>
            <div style="line-height:1.15;">
                <div style="font-weight:700; font-size:0.92rem;">{APP_NAME}</div>
                <div class="subtle" style="font-size:0.72rem;">Portfolio Platform</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_theme_toggle():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"

    current = st.session_state.theme_mode
    label = "Light mode" if current == "dark" else "Dark mode"

    if st.button(f"{'☀' if current == 'dark' else '🌙'}  {label}", width="stretch", key="theme_toggle_btn"):
        st.session_state.theme_mode = "light" if current == "dark" else "dark"
        st.rerun()


def render_sidebar_footer():
    st.markdown('<div class="nav-section-label">Connect</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display:flex; flex-direction:column; gap:0.4rem;">
            <a href="{GITHUB_URL}" target="_blank" style="text-decoration:none;">
                <div class="pill" style="width:100%; box-sizing:border-box; justify-content:flex-start;">
                    {icon('github', size=14)} GitHub Repository
                </div>
            </a>
            <a href="{LINKEDIN_URL}" target="_blank" style="text-decoration:none;">
                <div class="pill" style="width:100%; box-sizing:border-box; justify-content:flex-start;">
                    {icon('linkedin', size=14)} LinkedIn Profile
                </div>
            </a>
            <a href="mailto:mdimamuddinf786@gmail.com" style="text-decoration:none;">
            <div class="pill" style="width:100%; box-sizing:border-box; justify-content:flex-start;">
                📧 mdimamuddinf786@gmail.com
            </div>
        </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    if RESUME_PATH.exists():
        with open(RESUME_PATH, "rb") as f:
            st.download_button(
                "⬇ Download Résumé",
                data=f,
                file_name="resume.pdf",
                mime="application/pdf",
                width="stretch",
            )
    else:
        st.markdown(
            '<div class="pill pill-static" style="width:100%; box-sizing:border-box; justify-content:center;">'
            'Résumé PDF not uploaded yet</div>',
            unsafe_allow_html=True,
        )
