"""Statistics page: confidence intervals, hypothesis tests, and regression
diagnostics -- all computed live (cached), with interactive controls, not
static screenshots of the written report."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.icons import icon
from utils.data_loader import load_denormalized_startups
from utils.error_handler import safe_run
from utils.stats_engine import (
    mean_confidence_interval, bootstrap_median_ci, proportion_confidence_interval,
    two_proportion_ztest, chi_square_test, anova_and_tukey, fit_regression_with_diagnostics,
)


def _theme_template() -> str:
    return "plotly_dark" if st.session_state.get("theme_mode") == "dark" else "plotly_white"


def render_header():
    st.markdown(
        """
        <div class="pill pill-live"><span class="pill-dot"></span> Computed live with scipy / statsmodels — not static screenshots</div>
        <div style="height:0.5rem"></div>
        <h1 style="margin-bottom:0.1rem;">Statistical Analysis</h1>
        <p class="subtle" style="margin-top:0;">Confidence intervals, hypothesis tests, and a regression model with
        its assumptions actually checked — adjust the controls below and every result recomputes.</p>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Developed by Md Imamuddin")


@safe_run("Couldn't render the confidence intervals section.")
def section_confidence_intervals(df: pd.DataFrame):
    st.markdown("### 1. Confidence Intervals")
    confidence = st.select_slider("Confidence level", options=[0.90, 0.95, 0.99], value=0.95,
                                   format_func=lambda x: f"{int(x*100)}%")

    mean_ci = mean_confidence_interval(df["funding_total_usd"], confidence)
    median_ci = bootstrap_median_ci(df["funding_total_usd"], confidence)
    exit_ci = proportion_confidence_interval(int(df["is_exited"].sum()), len(df), confidence)

    rows = [
        {"metric": "Mean Funding", "point": mean_ci["point_estimate"], "low": mean_ci["ci_low"], "high": mean_ci["ci_high"]},
        {"metric": "Median Funding (bootstrap)", "point": median_ci["point_estimate"], "low": median_ci["ci_low"], "high": median_ci["ci_high"]},
    ]

    col1, col2 = st.columns([1.3, 1])
    with col1:
        fig = go.Figure()
        for i, r in enumerate(rows):
            fig.add_trace(go.Scatter(
                x=[r["low"], r["high"]], y=[r["metric"], r["metric"]],
                mode="lines", line=dict(color="#6366F1", width=6), showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=[r["point"]], y=[r["metric"]], mode="markers",
                marker=dict(color="#EC4899", size=12, symbol="diamond"), showlegend=False,
            ))
        fig.update_layout(
            title=f"{int(confidence*100)}% Confidence Intervals — Funding Amount",
            template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="USD", margin=dict(t=50, b=30, l=10, r=10), height=280,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with col2:
        st.markdown(
            f"""
            <div class="app-card">
                <div class="subtle" style="font-size:0.78rem;">EXIT RATE ({int(confidence*100)}% CI)</div>
                <div class="mono" style="font-size:1.4rem; font-weight:700; margin-top:0.2rem;">{exit_ci['point_estimate']*100:.2f}%</div>
                <div class="subtle" style="font-size:0.8rem; margin-top:0.3rem;">
                    ({exit_ci['ci_low']*100:.2f}% – {exit_ci['ci_high']*100:.2f}%), n={exit_ci['n']:,}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<p class="subtle" style="font-size:0.85rem;">
        Notice how much tighter the median's interval is relative to its size (±{(median_ci['ci_high']-median_ci['ci_low'])/2:,.0f})
        compared to the mean (±{(mean_ci['ci_high']-mean_ci['ci_low'])/2:,.0f}) — a direct consequence of funding's
        right-skew. The median is the more stable headline KPI.</p>""",
        unsafe_allow_html=True,
    )


@safe_run("Couldn't render the hypothesis testing section.")
def section_hypothesis_tests(df: pd.DataFrame):
    st.markdown("### 2. Hypothesis Tests")
    tab1, tab2, tab3 = st.tabs(["Two-Proportion Z-Test", "Chi-Square Test", "ANOVA + Tukey HSD"])

    with tab1:
        st.markdown('<p class="subtle">Compare exit rates between any country and the rest of the dataset.</p>', unsafe_allow_html=True)
        countries = df["country_name"].value_counts().head(30).index.tolist()
        selected = st.selectbox("Country to test", countries, index=countries.index("United States") if "United States" in countries else 0)

        group_a = df[df["country_name"] == selected]
        group_b = df[df["country_name"] != selected]
        result = two_proportion_ztest(
            int(group_a["is_exited"].sum()), len(group_a),
            int(group_b["is_exited"].sum()), len(group_b),
        )

        c1, c2, c3 = st.columns(3)
        c1.metric(f"{selected} exit rate", f"{result['rate_a']*100:.2f}%")
        c2.metric("Rest-of-world exit rate", f"{result['rate_b']*100:.2f}%")
        significant = result["p_value"] < 0.05
        c3.metric("p-value", f"{result['p_value']:.2e}", delta="Significant" if significant else "Not significant",
                   delta_color="normal" if significant else "off")
        st.markdown(f'<p class="subtle" style="font-size:0.85rem;">z = {result["z_stat"]:.2f}. '
                     f'{"This difference is statistically significant at α=0.05." if significant else "This difference is not statistically significant at α=0.05."}</p>',
                     unsafe_allow_html=True)

    with tab2:
        st.markdown('<p class="subtle">Tests whether industry category and outcome status are independent.</p>', unsafe_allow_html=True)
        top_n = st.slider("Number of top industries to include", 4, 15, 8)
        result = chi_square_test(df, "primary_category", "status", top_n=top_n)

        significant = result["p_value"] < 0.05
        c1, c2, c3 = st.columns(3)
        c1.metric("χ²", f"{result['chi2']:.1f}")
        c2.metric("Degrees of freedom", result["dof"])
        c3.metric("p-value", f"{result['p_value']:.2e}", delta="Significant" if significant else "Not significant",
                   delta_color="normal" if significant else "off")

        fig = px.imshow(result["crosstab"], text_auto=True, aspect="auto",
                         color_continuous_scale=["#0A0E17", "#6366F1"] if st.session_state.get("theme_mode") == "dark" else ["#F7F8FA", "#4F46E5"],
                         title="Industry × Status Contingency Table")
        fig.update_layout(template=_theme_template(), paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=50, b=10, l=10, r=10), height=420)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with tab3:
        st.markdown('<p class="subtle">Does funding amount differ significantly across funding-stage groups?</p>', unsafe_allow_html=True)
        result = anova_and_tukey(df, "furthest_stage_category", "funding_total_usd")

        significant = result["p_value"] < 0.05
        c1, c2 = st.columns(2)
        c1.metric("F-statistic", f"{result['f_stat']:.1f}")
        c2.metric("p-value", f"{result['p_value']:.2e}", delta="Significant" if significant else "Not significant",
                   delta_color="normal" if significant else "off")

        box_data = result["box_data"].copy()
        box_data["log_funding"] = np.log1p(box_data["funding_total_usd"])
        fig = px.box(box_data, x="furthest_stage_category", y="log_funding", color="furthest_stage_category",
                     title="log(Funding) by Furthest Stage Reached", template=_theme_template(),
                     color_discrete_sequence=["#6366F1", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981", "#3B82F6", "#8B92A8"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                           margin=dict(t=50, b=30, l=10, r=10), height=380, xaxis_title="", yaxis_title="log(1 + Funding USD)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        with st.expander("Tukey HSD post-hoc pairwise comparisons"):
            st.dataframe(result["tukey_df"], width="stretch", hide_index=True)
            n_sig = (result["tukey_df"]["reject"] == "True").sum() if "reject" in result["tukey_df"].columns else None
            if n_sig is not None:
                st.markdown(f'<p class="subtle" style="font-size:0.85rem;">{n_sig} of {len(result["tukey_df"])} '
                             f'pairwise comparisons are statistically significant at α=0.05.</p>', unsafe_allow_html=True)


@safe_run("Couldn't render the regression diagnostics section.")
def section_regression(df: pd.DataFrame):
    st.markdown("### 3. Regression Model & Assumption Diagnostics")
    st.markdown('<p class="subtle">Predicting log(funding) from company profile — with assumptions actually checked, not assumed.</p>', unsafe_allow_html=True)

    top_n = st.slider("Number of industries included in model", 3, 10, 6, key="reg_top_n")

    with st.spinner("Fitting OLS regression..."):
        result = fit_regression_with_diagnostics(df, top_n_industries=top_n)

    c1, c2, c3 = st.columns(3)
    c1.metric("R²", f"{result['r_squared']:.3f}")
    c2.metric("Adjusted R²", f"{result['adj_r_squared']:.3f}")
    c3.metric("Observations", f"{result['n_obs']:,}")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Scatter(
            x=result["fitted"], y=result["resid"], mode="markers",
            marker=dict(color="#6366F1", size=4, opacity=0.35),
        ))
        fig.add_hline(y=0, line_color="#EF4444", line_width=1.5)
        fig.update_layout(title="Residuals vs. Fitted", template=_theme_template(),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           xaxis_title="Fitted (log funding)", yaxis_title="Residual",
                           margin=dict(t=50, b=30, l=10, r=10), height=340)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with col2:
        from scipy import stats as sp_stats
        osm, osr = sp_stats.probplot(result["resid"], dist="norm", fit=False)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=osm, y=osr, mode="markers",
                                   marker=dict(color="#8B5CF6", size=4, opacity=0.4), name="Residuals"))
        line_x = np.array([osm.min(), osm.max()])
        slope, intercept = np.polyfit(osm, osr, 1)
        fig2.add_trace(go.Scatter(x=line_x, y=slope * line_x + intercept, mode="lines",
                                   line=dict(color="#EF4444", width=1.5), name="Normal line"))
        fig2.update_layout(title="Q-Q Plot of Residuals", template=_theme_template(),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            xaxis_title="Theoretical quantiles", yaxis_title="Sample quantiles",
                            showlegend=False, margin=dict(t=50, b=30, l=10, r=10), height=340)
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

    st.markdown("#### Assumption diagnostics")
    d1, d2, d3 = st.columns(3)
    with d1:
        max_vif = result["vif"]["VIF"].max()
        ok = max_vif < 5
        st.markdown(
            f"""<div class="app-card"><div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:0.85rem;">Multicollinearity (VIF)</strong>
            <span class="pill {'pill-live' if ok else 'pill-warn'}"><span class="pill-dot"></span>{'OK' if ok else 'Check'}</span></div>
            <div class="mono" style="font-size:1.1rem; margin-top:0.4rem;">max VIF = {max_vif:.2f}</div>
            <p class="subtle" style="font-size:0.78rem; margin-top:0.3rem;">Threshold: VIF &lt; 5 is generally fine.</p></div>""",
            unsafe_allow_html=True,
        )
    with d2:
        bp_p = result["bp_lm_pvalue"]
        violated = bp_p < 0.05
        st.markdown(
            f"""<div class="app-card"><div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:0.85rem;">Homoscedasticity</strong>
            <span class="pill {'pill-warn' if violated else 'pill-live'}"><span class="pill-dot"></span>{'Violated' if violated else 'OK'}</span></div>
            <div class="mono" style="font-size:1.1rem; margin-top:0.4rem;">BP p = {bp_p:.2e}</div>
            <p class="subtle" style="font-size:0.78rem; margin-top:0.3rem;">p &lt; 0.05 = residual variance not constant.</p></div>""",
            unsafe_allow_html=True,
        )
    with d3:
        sh_p = result["shapiro_pvalue"]
        violated = sh_p < 0.05
        st.markdown(
            f"""<div class="app-card"><div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:0.85rem;">Normality of Residuals</strong>
            <span class="pill {'pill-warn' if violated else 'pill-live'}"><span class="pill-dot"></span>{'Violated' if violated else 'OK'}</span></div>
            <div class="mono" style="font-size:1.1rem; margin-top:0.4rem;">Shapiro p = {sh_p:.2e}</div>
            <p class="subtle" style="font-size:0.78rem; margin-top:0.3rem;">Expected to trip at large n; point estimates remain usable.</p></div>""",
            unsafe_allow_html=True,
        )

    with st.expander("Full coefficient table"):
        st.dataframe(result["coef_table"].round(4), width="stretch")

    st.markdown(
        """<div class="app-card" style="margin-top:0.8rem; display:flex; gap:0.7rem; align-items:flex-start;">
        <span style="font-size:1.1rem;">⚠</span>
        <p class="subtle" style="margin:0; font-size:0.83rem;">Heteroscedasticity, when flagged above, means exact
        p-values/CIs are approximate rather than precise — coefficients and their signs remain trustworthy given the
        large sample size. A production model would refit with heteroscedasticity-robust standard errors.</p></div>""",
        unsafe_allow_html=True,
    )


def render():
    render_header()
    df = load_denormalized_startups()

    section_confidence_intervals(df)
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    section_hypothesis_tests(df)
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    section_regression(df)
