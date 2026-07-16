"""Gradient KPI card component -- the signature visual element of the app."""
import streamlit as st

from components.icons import icon


def kpi_card(label: str, value: str, delta: str = None, gradient: int = 1, icon_name: str = "trending-up"):
    """Renders one gradient KPI card. gradient is 1-6, mapping to .kpi-grad-N in theme.py."""
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="kpi-card kpi-grad-{gradient}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; position:relative; z-index:1;">
                <div class="kpi-label">{label}</div>
                {icon(icon_name, size=16)}
            </div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list):
    """items: list of dicts with keys label, value, delta (optional), gradient, icon_name"""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            kpi_card(
                label=item["label"],
                value=item["value"],
                delta=item.get("delta"),
                gradient=item.get("gradient", 1),
                icon_name=item.get("icon_name", "trending-up"),
            )


def skeleton_row(n: int = 6):
    """Loading skeleton placeholders shown while data loads."""
    cols = st.columns(n)
    for col in cols:
        with col:
            st.markdown('<div class="skeleton"></div>', unsafe_allow_html=True)
