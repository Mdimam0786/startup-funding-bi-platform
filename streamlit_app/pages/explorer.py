"""Explorer page: search and browse startups, investors, countries, and
industries directly -- AgGrid-powered tables with search, filtering,
pagination, row selection, and CSV export in every tab."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from utils.data_loader import load_csv, load_denormalized_startups
from utils.error_handler import safe_run


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def _aggrid_theme() -> str:
    return "alpine-dark" if st.session_state.get("theme_mode") == "dark" else "alpine"


def _fmt_money(x) -> str:
    if pd.isna(x):
        return "—"
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    if x >= 1e6:
        return f"${x/1e6:.2f}M"
    if x >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


def render_header():
    st.markdown(
    """
    <div class="pill pill-live">
        <span class="pill-dot"></span>
        AgGrid-powered · search, filter, sort, paginate, export
    </div>

    <div style="height:0.5rem"></div>

    <h1 style="margin-bottom:0.1rem;">
        Explorer
    </h1>
    """,
    unsafe_allow_html=True,
)

st.caption("Developed by Md Imamuddin")

st.markdown(
    """
    <p class="subtle">
    Search the full dataset directly...
    </p>
    """,
    unsafe_allow_html=True,
)
    
    


def _grid(df: pd.DataFrame, page_size: int = 12, selectable: bool = False, height: int = 420):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)
    gb.configure_default_column(sortable=True, filter=True, resizable=True)
    if selectable:
        gb.configure_selection(selection_mode="single", use_checkbox=False)
    grid_response = AgGrid(
        df, gridOptions=gb.build(), height=height, theme=_aggrid_theme(),
        update_mode=GridUpdateMode.SELECTION_CHANGED if selectable else GridUpdateMode.NO_UPDATE,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True, allow_unsafe_jscode=False,
    )
    return grid_response


@safe_run("Couldn't render the startup search tab.")
def tab_startups(df: pd.DataFrame):
    st.markdown('<p class="subtle">Search by name, filter by industry/country/status, click a row for detail.</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1])
    with c1:
        search = st.text_input("Search startup name", placeholder="e.g. \"Uber\", \"Slack\"", key="startup_search")
    with c2:
        status_filter = st.selectbox("Status", ["All"] + sorted(df["status"].dropna().unique().tolist()), key="startup_status")
    with c3:
        unicorn_only = st.checkbox("Unicorns only", key="startup_unicorn")
    with c4:
        min_funding = st.number_input("Min funding ($M)", min_value=0, value=0, step=1, key="startup_min_funding")

    view = df.copy()
    if search:
        view = view[view["name"].str.contains(search, case=False, na=False)]
    if status_filter != "All":
        view = view[view["status"] == status_filter]
    if unicorn_only:
        view = view[view["is_unicorn"] == True]  # noqa: E712
    if min_funding > 0:
        view = view[view["funding_total_usd"] >= min_funding * 1e6]

    display_cols = ["name", "country_name", "primary_category", "status", "funding_total_usd", "funding_rounds", "is_unicorn"]
    display = view[display_cols].rename(columns={
        "name": "Name", "country_name": "Country", "primary_category": "Industry", "status": "Status",
        "funding_total_usd": "Total Funding", "funding_rounds": "Rounds", "is_unicorn": "Unicorn",
    }).sort_values("Total Funding", ascending=False)

    st.markdown(f'<p class="subtle" style="font-size:0.82rem;">{len(display):,} of {len(df):,} startups match.</p>', unsafe_allow_html=True)
    response = _grid(display, selectable=True)

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download results (CSV)", data=csv, file_name="startup_search_results.csv", mime="text/csv", key="dl_startups")

    selected = response.get("selected_rows") if isinstance(response, dict) else getattr(response, "selected_rows", None)
    if selected is not None and len(selected) > 0:
        row = selected.iloc[0] if hasattr(selected, "iloc") else selected[0]
        name = row["Name"] if isinstance(row, dict) else row.get("Name")
        st.markdown("#### Selected startup")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Name", row["Name"] if isinstance(row, dict) else row.get("Name"))
        d2.metric("Country", row["Country"] if isinstance(row, dict) else row.get("Country"))
        d3.metric("Industry", row["Industry"] if isinstance(row, dict) else row.get("Industry"))
        d4.metric("Total Funding", _fmt_money(row["Total Funding"] if isinstance(row, dict) else row.get("Total Funding")))


@safe_run("Couldn't render the investor search tab.")
def tab_investors():
    st.markdown('<p class="subtle">Search unicorn-portfolio investors (see the scope note at the bottom of this tab).</p>', unsafe_allow_html=True)

    investors = load_csv("investor")
    bridge = load_csv("investor_bridge")

    portfolio = bridge.groupby("investor_id").agg(portfolio_count=("company", "nunique")).reset_index()
    merged = investors.merge(portfolio, on="investor_id", how="left").fillna({"portfolio_count": 0})
    merged["portfolio_count"] = merged["portfolio_count"].astype(int)

    search = st.text_input("Search investor name", placeholder="e.g. \"Sequoia\", \"Andreessen\"", key="investor_search")
    view = merged.copy()
    if search:
        view = view[view["investor_name"].str.contains(search, case=False, na=False)]
    view = view.sort_values("portfolio_count", ascending=False)

    display = view[["investor_name", "portfolio_count"]].rename(columns={"investor_name": "Investor", "portfolio_count": "Unicorn Portfolio Count"})
    st.markdown(f'<p class="subtle" style="font-size:0.82rem;">{len(display):,} investors match.</p>', unsafe_allow_html=True)
    _grid(display, page_size=10)

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download results (CSV)", data=csv, file_name="investor_search_results.csv", mime="text/csv", key="dl_investors")

    top15 = merged.sort_values("portfolio_count", ascending=False).head(15).sort_values("portfolio_count")
    fig = go.Figure(go.Bar(x=top15["portfolio_count"], y=top15["investor_name"], orientation="h", marker_color="#7048E8"))
    fig.update_layout(title="Top 15 Investors by Unicorn Portfolio Count", template=_theme_template(),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       margin=dict(t=50, b=30, l=10, r=10), height=420)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown(
        """<div class="app-card" style="margin-top:0.5rem;">
        <strong style="font-size:0.83rem;">Scope note</strong>
        <p class="subtle" style="margin:0.3rem 0 0 0; font-size:0.8rem;">Investor data only covers the 254
        startups matched to the global unicorn list — not the full 67,098-startup dataset.</p></div>""",
        unsafe_allow_html=True,
    )


@safe_run("Couldn't render the country search tab.")
def tab_countries(df: pd.DataFrame):
    st.markdown('<p class="subtle">Select a country to see its funding profile, top startups, and position on the map.</p>', unsafe_allow_html=True)

    country_stats = df.dropna(subset=["country_name"]).groupby("country_name").agg(
        total_funding=("funding_total_usd", "sum"), startups=("startup_id", "count"),
        unicorns=("is_unicorn", "sum"), exit_rate=("is_exited", "mean"),
    ).reset_index().sort_values("total_funding", ascending=False)

    search = st.text_input("Search country", placeholder="e.g. \"United States\", \"India\"", key="country_search")
    view = country_stats.copy()
    if search:
        view = view[view["country_name"].str.contains(search, case=False, na=False)]

    col1, col2 = st.columns([1.3, 1])
    with col1:
        display = view.rename(columns={
            "country_name": "Country", "total_funding": "Total Funding", "startups": "Startups",
            "unicorns": "Unicorns", "exit_rate": "Exit Rate",
        })
        display["Exit Rate"] = (display["Exit Rate"] * 100).round(1).astype(str) + "%"
        st.markdown(f'<p class="subtle" style="font-size:0.82rem;">{len(display):,} countries match.</p>', unsafe_allow_html=True)
        _grid(display, page_size=10, height=440)
        csv = display.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download results (CSV)", data=csv, file_name="country_search_results.csv", mime="text/csv", key="dl_countries")

    with col2:
        highlight = view["country_name"].tolist() if search else country_stats.head(15)["country_name"].tolist()
        map_data = country_stats[country_stats["country_name"].isin(highlight)]
        fig = px.choropleth(
            map_data, locations="country_name", locationmode="country names", color="total_funding",
            color_continuous_scale=["#E7F5FF", "#0B4F8A"], template=_theme_template(),
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10), height=440,
                           geo=dict(bgcolor="rgba(0,0,0,0)"), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't render the industry search tab.")
def tab_industries(df: pd.DataFrame):
    st.markdown('<p class="subtle">Select an industry to see its funding profile and outcome mix.</p>', unsafe_allow_html=True)

    ind_stats = df.dropna(subset=["primary_category"]).groupby("primary_category").agg(
        total_funding=("funding_total_usd", "sum"), startups=("startup_id", "count"),
        unicorns=("is_unicorn", "sum"), exit_rate=("is_exited", "mean"),
    ).query("startups >= 5").reset_index().sort_values("total_funding", ascending=False)

    search = st.text_input("Search industry", placeholder="e.g. \"Software\", \"Biotech\"", key="industry_search")
    view = ind_stats.copy()
    if search:
        view = view[view["primary_category"].str.contains(search, case=False, na=False)]

    display = view.rename(columns={
        "primary_category": "Industry", "total_funding": "Total Funding", "startups": "Startups",
        "unicorns": "Unicorns", "exit_rate": "Exit Rate",
    })
    display["Exit Rate"] = (display["Exit Rate"] * 100).round(1).astype(str) + "%"
    st.markdown(f'<p class="subtle" style="font-size:0.82rem;">{len(display):,} industries match.</p>', unsafe_allow_html=True)
    _grid(display, page_size=12)

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download results (CSV)", data=csv, file_name="industry_search_results.csv", mime="text/csv", key="dl_industries")

    if len(view) > 0:
        top20 = view.head(20).sort_values("total_funding")
        fig = go.Figure(go.Bar(x=top20["total_funding"], y=top20["primary_category"], orientation="h",
                                marker_color="#4F46E5"))
        fig.update_layout(title=f"Total Funding by Industry ({len(top20)} shown)", template=_theme_template(),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=50, b=30, l=10, r=10), height=460)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render():
    render_header()
    df = load_denormalized_startups()

    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Startups", "💼 Investors", "🌍 Countries", "🏭 Industries"])
    with tab1:
        tab_startups(df)
    with tab2:
        tab_investors()
    with tab3:
        tab_countries(df)
    with tab4:
        tab_industries(df)
