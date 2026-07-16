"""EDA page: interactive filtered charts across funding, industry, geography,
and stage/outcome dimensions, plus a searchable/paginated table of all 101
written insights from the EDA report."""
from components.footer import render_footer
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from config.settings import DATA_SCOPE_NOTE
from utils.data_loader import load_csv, load_denormalized_startups, get_filter_options
from utils.eda_parser import load_insights
from utils.error_handler import safe_run


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def _fmt_money(x: float) -> str:
    if pd.isna(x):
        return "—"
    if x >= 1e9:
        return f"${x/1e9:.1f}B"
    if x >= 1e6:
        return f"${x/1e6:.1f}M"
    if x >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


def render_header():
    st.markdown(
    """
    <div class="pill pill-live">
        <span class="pill-dot"></span>
        101 insights · sourced from src/eda/compute_eda_stats.py
    </div>

    <div style="height:0.5rem"></div>

    <h1 style="margin-bottom:0.1rem;">
        Exploratory Data Analysis
    </h1>
    """,
    unsafe_allow_html=True,
)



st.markdown(
    """
    <p class="subtle" style="margin-top:0;">
    Filter the dataset live and watch every chart update — this is the same
    data behind the 101 written insights below, not a separate static export.
    </p>
    """,
    unsafe_allow_html=True,
)
    

@safe_run("Couldn't build the filter panel.")
def render_filters(df: pd.DataFrame):
    st.markdown("#### Filters")
    c1, c2, c3 = st.columns([1.3, 1.3, 1])

    with c1:
        countries = get_filter_options(df, "country_name")
        selected_countries = st.multiselect(
            "Country", options=countries, default=[], placeholder="All countries",
        )
    with c2:
        industries = get_filter_options(df, "primary_category")
        selected_industries = st.multiselect(
            "Industry", options=industries, default=[], placeholder="All industries",
        )
    with c3:
        min_year, max_year = 1995, 2015
        year_range = st.slider("Founded/funded year range", min_year, max_year, (min_year, max_year))

    filtered = df.copy()
    if selected_countries:
        filtered = filtered[filtered["country_name"].isin(selected_countries)]
    if selected_industries:
        filtered = filtered[filtered["primary_category"].isin(selected_industries)]

    date_dim = load_csv("date")
    filtered = filtered.merge(date_dim[["date_id", "year"]], left_on="first_funding_date_id", right_on="date_id", how="left")
    filtered = filtered[filtered["year"].between(year_range[0], year_range[1]) | filtered["year"].isna()]

    return filtered, (selected_countries, selected_industries, year_range)


@safe_run("Couldn't render the filtered summary row.")
def render_filtered_summary(filtered: pd.DataFrame, full_df: pd.DataFrame):
    n = len(filtered)
    pct = n / len(full_df) * 100
    total_funding = filtered["funding_total_usd"].sum()
    median_funding = filtered["funding_total_usd"].median()
    exit_rate = filtered["is_exited"].mean() if n else 0

    st.markdown(
        f"""
        <div class="app-card" style="display:flex; gap:2.2rem; align-items:center; flex-wrap:wrap; padding:1rem 1.4rem;">
            <div><span class="subtle" style="font-size:0.78rem;">MATCHING STARTUPS</span><br>
                <span class="mono" style="font-weight:700; font-size:1.15rem;">{n:,}</span>
                <span class="subtle" style="font-size:0.78rem;"> ({pct:.1f}% of dataset)</span></div>
            <div><span class="subtle" style="font-size:0.78rem;">TOTAL FUNDING</span><br>
                <span class="mono" style="font-weight:700; font-size:1.15rem;">{_fmt_money(total_funding)}</span></div>
            <div><span class="subtle" style="font-size:0.78rem;">MEDIAN FUNDING</span><br>
                <span class="mono" style="font-weight:700; font-size:1.15rem;">{_fmt_money(median_funding)}</span></div>
            <div><span class="subtle" style="font-size:0.78rem;">EXIT RATE</span><br>
                <span class="mono" style="font-weight:700; font-size:1.15rem;">{exit_rate*100:.1f}%</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@safe_run("Couldn't render the funding trend tab.")
def tab_funding_trends(filtered: pd.DataFrame):
    yearly = (
        filtered[filtered["year"].between(1995, 2015)]
        .groupby("year")
        .agg(total_funding=("funding_total_usd", "sum"), deals=("startup_id", "count"))
        .reset_index()
    )
    if yearly.empty:
        st.info("No data matches the current filters.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(x=yearly["year"], y=yearly["total_funding"], name="Total Funding", marker_color="#6366F1"))
    fig.add_trace(go.Scatter(x=yearly["year"], y=yearly["deals"], name="Deal Count", mode="lines+markers",
                              line=dict(color="#EC4899", width=3), yaxis="y2"))
    fig.update_layout(
        template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Total Funding (USD)"), yaxis2=dict(title="Deal Count", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.08), margin=dict(t=30, b=30, l=10, r=10), height=420, hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    median_by_year = filtered[filtered["year"].between(2000, 2015)].groupby("year")["funding_total_usd"].median().reset_index()
    fig2 = px.line(median_by_year, x="year", y="funding_total_usd", markers=True,
                    title="Median Deal Size by Year (log scale)", template=_theme_template())
    fig2.update_traces(line_color="#8B5CF6")
    fig2.update_layout(yaxis_type="log", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=50, b=30, l=10, r=10), height=340)
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't render the industry tab.")
def tab_industries(filtered: pd.DataFrame):
    ind = (
        filtered.groupby("primary_category")
        .agg(startups=("startup_id", "count"), total_funding=("funding_total_usd", "sum"), exit_rate=("is_exited", "mean"))
        .query("startups >= 10")
        .sort_values("total_funding", ascending=False)
        .head(15)
    )
    if ind.empty:
        st.info("No industries with ≥10 startups match the current filters.")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(ind.sort_values("total_funding"), x="total_funding", y=ind.sort_values("total_funding").index,
                      orientation="h", title="Top 15 Industries by Total Funding", template=_theme_template(),
                      color="total_funding", color_continuous_scale=["#C7D2FE", "#4F46E5"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
                           margin=dict(t=50, b=30, l=10, r=10), height=440, yaxis_title="", xaxis_title="Total Funding")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with col2:
        fig2 = px.scatter(ind.reset_index(), x="startups", y="exit_rate", size="total_funding", color="total_funding",
                           hover_name="primary_category", title="Volume vs. Exit Rate (bubble = funding)",
                           template=_theme_template(), color_continuous_scale=["#C7D2FE", "#4F46E5"])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
                            margin=dict(t=50, b=30, l=10, r=10), height=440,
                            xaxis_title="Number of Startups", yaxis_title="Exit Rate")
        fig2.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't render the geography tab.")
def tab_geography(filtered: pd.DataFrame):
    ctry = (
        filtered.groupby("country_name")
        .agg(startups=("startup_id", "count"), total_funding=("funding_total_usd", "sum"))
        .sort_values("total_funding", ascending=False)
        .head(15)
    )
    if ctry.empty:
        st.info("No data matches the current filters.")
        return

    fig = px.choropleth(
        filtered.groupby("country_name").agg(total_funding=("funding_total_usd", "sum")).reset_index(),
        locations="country_name", locationmode="country names", color="total_funding",
        color_continuous_scale=["#E7F5FF", "#0B4F8A"], title="Total Funding by Country",
        template=_theme_template(),
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50, b=10, l=10, r=10), height=420,
                       geo=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    fig2 = px.bar(ctry.reset_index(), x="total_funding", y="country_name", orientation="h",
                   title="Top 15 Countries by Total Funding", template=_theme_template(),
                   color="total_funding", color_continuous_scale=["#FBCFE8", "#DB2777"])
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
                        margin=dict(t=50, b=30, l=10, r=10), height=440, yaxis=dict(autorange="reversed"), yaxis_title="")
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})


@safe_run("Couldn't render the stage & outcomes tab.")
def tab_stage_outcomes(filtered: pd.DataFrame):
    col1, col2 = st.columns(2)
    with col1:
        stage_order = ["Early Stage", "Venture", "Growth", "Late Stage / Public"]
        stage_counts = filtered["furthest_stage_category"].value_counts().reindex(stage_order).dropna()
        if stage_counts.empty:
            st.info("No staged startups match the current filters.")
        else:
            fig = go.Figure(go.Funnel(
                y=stage_counts.index, x=stage_counts.values,
                marker=dict(color=["#4338CA", "#6366F1", "#A5B4FC", "#E0E7FF"]),
            ))
            fig.update_layout(title="Funding Stage Funnel", template=_theme_template(),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=50, b=20, l=10, r=10), height=400)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with col2:
        status_counts = filtered["status"].value_counts()
        if status_counts.empty:
            st.info("No data matches the current filters.")
        else:
            fig2 = px.pie(values=status_counts.values, names=status_counts.index, hole=0.55,
                           title="Status Breakdown", template=_theme_template(),
                           color_discrete_sequence=["#6366F1", "#8B92A8", "#10B981", "#F59E0B"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50, b=20, l=10, r=10), height=400)
            st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

    st.markdown(
        """<div class="app-card" style="margin-top:0.5rem;">
        <strong style="font-size:0.85rem;">⚠ Survivorship caveat</strong>
        <p class="subtle" style="margin:0.3rem 0 0 0; font-size:0.82rem;">Newer cohorts show lower exit rates
        mainly because they've had less time to reach an outcome as of this 2015 data snapshot — not because
        they performed worse. See EDA report §Cohort Analysis for the full breakdown.</p></div>""",
        unsafe_allow_html=True,
    )


@safe_run("Couldn't render the insights explorer.")
def render_insights_explorer():
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    st.markdown("### Insights Explorer")
    st.markdown('<p class="subtle">Search or filter all 101 written insights — same numbering as the full EDA report.</p>', unsafe_allow_html=True)

    insights_df = load_insights()

    c1, c2 = st.columns([2, 1])
    with c1:
        search_term = st.text_input("Search insights", placeholder="e.g. \"unicorn\", \"exit rate\", \"median\"",
                                     icon="🔍")
    with c2:
        sections = ["All sections"] + sorted(insights_df["section"].unique().tolist())
        section_filter = st.selectbox("Section", sections)

    view = insights_df.copy()
    if search_term:
        view = view[view["insight"].str.contains(search_term, case=False, na=False)]
    if section_filter != "All sections":
        view = view[view["section"] == section_filter]

    st.markdown(f'<p class="subtle" style="font-size:0.82rem;">{len(view)} of {len(insights_df)} insights match.</p>', unsafe_allow_html=True)

    gb = GridOptionsBuilder.from_dataframe(view[["number", "section", "insight"]])
    gb.configure_column("number", header_name="#", width=70, pinned="left")
    gb.configure_column("section", header_name="Section", width=260, wrapText=True, autoHeight=True)
    gb.configure_column("insight", header_name="Insight", flex=3, wrapText=True, autoHeight=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_default_column(sortable=True, filter=True, resizable=True)
    grid_options = gb.build()

    AgGrid(
        view[["number", "section", "insight"]],
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme="alpine-dark" if st.session_state.get("theme_mode") == "dark" else "alpine",
        height=460,
        fit_columns_on_grid_load=True,
    )

    csv = view.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download filtered insights (CSV)", data=csv, file_name="eda_insights_filtered.csv", mime="text/csv")


def render():
    render_header()
    df = load_denormalized_startups()

    filtered, filter_state = render_filters(df)
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    render_filtered_summary(filtered, df)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Funding Trends", "🏭 Industries", "🌍 Geography", "🏁 Stage & Outcomes"])
    with tab1:
        tab_funding_trends(filtered)
    with tab2:
        tab_industries(filtered)
    with tab3:
        tab_geography(filtered)
    with tab4:
        tab_stage_outcomes(filtered)

    render_insights_explorer()

    st.markdown(
        f"""<div class="app-card" style="margin-top:1rem; display:flex; align-items:flex-start; gap:0.7rem;">
        {icon('info', size=18)}
        <div><strong style="font-size:0.88rem;">Data scope</strong>
        <p class="subtle" style="margin:0.2rem 0 0 0; font-size:0.85rem;">{DATA_SCOPE_NOTE}</p></div></div>""",
        unsafe_allow_html=True,
    )
    render_footer()
