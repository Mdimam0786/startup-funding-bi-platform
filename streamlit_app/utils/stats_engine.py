"""
Cached statistical computations. Every function here is st.cache_data'd
because Streamlit reruns the whole script on every widget interaction --
without caching, a bootstrap CI or OLS refit would recompute on every
click, which is both slow and pointless when the inputs haven't changed.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.proportion import proportions_ztest

sys.path.append(str(Path(__file__).resolve().parent.parent))


@st.cache_data(show_spinner=False)
def mean_confidence_interval(values: pd.Series, confidence: float = 0.95):
    s = values.dropna()
    n = len(s)
    mean = s.mean()
    sem = stats.sem(s)
    ci = stats.t.interval(confidence, n - 1, loc=mean, scale=sem)
    return {"point_estimate": mean, "ci_low": ci[0], "ci_high": ci[1], "n": n}


@st.cache_data(show_spinner=False)
def bootstrap_median_ci(values: pd.Series, confidence: float = 0.95, n_boot: int = 1500, seed: int = 42):
    arr = values.dropna().values
    rng = np.random.RandomState(seed)
    boot_medians = [np.median(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1 - confidence) / 2
    lo, hi = np.percentile(boot_medians, [alpha * 100, (1 - alpha) * 100])
    return {"point_estimate": float(np.median(arr)), "ci_low": float(lo), "ci_high": float(hi), "n": len(arr)}


@st.cache_data(show_spinner=False)
def proportion_confidence_interval(successes: int, n: int, confidence: float = 0.95):
    p = successes / n
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    se = np.sqrt(p * (1 - p) / n)
    return {"point_estimate": p, "ci_low": p - z * se, "ci_high": p + z * se, "n": n}


@st.cache_data(show_spinner=False)
def two_proportion_ztest(count_a: int, n_a: int, count_b: int, n_b: int):
    count = np.array([count_a, count_b])
    nobs = np.array([n_a, n_b])
    z_stat, p_val = proportions_ztest(count, nobs)
    return {
        "rate_a": count_a / n_a, "rate_b": count_b / n_b,
        "z_stat": float(z_stat), "p_value": float(p_val),
    }


@st.cache_data(show_spinner=False)
def chi_square_test(df: pd.DataFrame, cat_col: str, target_col: str, top_n: int = 8):
    top_categories = df[cat_col].value_counts().head(top_n).index
    sub = df[df[cat_col].isin(top_categories)]
    ct = pd.crosstab(sub[cat_col], sub[target_col])
    chi2, p_val, dof, expected = stats.chi2_contingency(ct)
    return {"crosstab": ct, "chi2": float(chi2), "p_value": float(p_val), "dof": int(dof)}


@st.cache_data(show_spinner=False)
def anova_and_tukey(df: pd.DataFrame, group_col: str, value_col: str, min_group_size: int = 30):
    sub = df[[group_col, value_col]].dropna()
    counts = sub[group_col].value_counts()
    valid = counts[counts >= min_group_size].index
    sub = sub[sub[group_col].isin(valid)]

    groups = [g[value_col].values for _, g in sub.groupby(group_col)]
    f_stat, p_val = stats.f_oneway(*groups)

    tukey = pairwise_tukeyhsd(sub[value_col], sub[group_col], alpha=0.05)
    tukey_df = pd.DataFrame(
        data=tukey.summary().data[1:], columns=tukey.summary().data[0]
    )
    return {"f_stat": float(f_stat), "p_value": float(p_val), "tukey_df": tukey_df, "box_data": sub}


@st.cache_data(show_spinner=False)
def fit_regression_with_diagnostics(df: pd.DataFrame, top_n_industries: int = 6, sample_size: int = 10000, seed: int = 42):
    model_df = df[[
        "log_funding_total_usd", "funding_rounds", "years_since_founded",
        "is_multi_round", "category_count", "primary_category",
    ]].dropna()

    top_industries = model_df["primary_category"].value_counts().head(top_n_industries).index
    model_df = model_df[model_df["primary_category"].isin(top_industries)].copy()
    model_df["is_multi_round"] = model_df["is_multi_round"].astype(int)

    if len(model_df) > sample_size:
        model_df = model_df.sample(n=sample_size, random_state=seed)

    formula = "log_funding_total_usd ~ funding_rounds + years_since_founded + is_multi_round + category_count + C(primary_category)"
    model = smf.ols(formula, data=model_df).fit()

    X = model_df[["funding_rounds", "years_since_founded", "category_count"]].copy()
    X["is_multi_round"] = model_df["is_multi_round"]
    X = sm.add_constant(X)
    vif_data = pd.DataFrame()
    vif_data["feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]

    bp_test = het_breuschpagan(model.resid, model.model.exog)

    resid_sample = model.resid if len(model.resid) <= 5000 else model.resid.sample(5000, random_state=seed)
    shapiro_stat, shapiro_p = stats.shapiro(resid_sample)

    return {
        "model": model,
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "n_obs": int(model.nobs),
        "fitted": model.fittedvalues,
        "resid": model.resid,
        "vif": vif_data,
        "bp_lm_stat": bp_test[0], "bp_lm_pvalue": bp_test[1],
        "shapiro_stat": shapiro_stat, "shapiro_pvalue": shapiro_p,
        "coef_table": model.summary2().tables[1],
    }
