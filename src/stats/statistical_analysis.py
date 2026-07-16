"""
Statistical Analysis.

Goes beyond the descriptive EDA into formal inferential statistics:
confidence intervals, hypothesis tests (t-tests, chi-square, ANOVA +
post-hoc), and a regression model with full assumption diagnostics.
"""
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.proportion import proportions_ztest

WH = str(Path(__file__).resolve().parents[2] / "data" / "warehouse") + "/"
fact = pd.read_csv(WH + "fact_startup_funding.csv", low_memory=False)
startup = pd.read_csv(WH + "dim_startup_with_source_key.csv", low_memory=False)
geo = pd.read_csv(WH + "dim_geography.csv", low_memory=False)
industry = pd.read_csv(WH + "dim_industry.csv", low_memory=False)

df = fact.merge(startup, on="startup_id").merge(geo, on="geography_id", how="left").merge(industry, on="industry_id", how="left")

print("="*80); print("1. CONFIDENCE INTERVALS"); print("="*80)

def mean_ci(series, confidence=0.95):
    s = series.dropna()
    n = len(s)
    mean = s.mean()
    sem = stats.sem(s)
    ci = stats.t.interval(confidence, n-1, loc=mean, scale=sem)
    return mean, ci, n

mean, ci, n = mean_ci(df['funding_total_usd'])
print(f"Mean funding_total_usd: ${mean:,.0f}, 95% CI: (${ci[0]:,.0f}, ${ci[1]:,.0f}), n={n:,}")

# Median CI via bootstrap (median has no simple closed-form CI)
np.random.seed(42)
fund = df['funding_total_usd'].dropna().values
boot_medians = [np.median(np.random.choice(fund, size=len(fund), replace=True)) for _ in range(2000)]
median_ci = np.percentile(boot_medians, [2.5, 97.5])
print(f"Median funding_total_usd: ${np.median(fund):,.0f}, 95% bootstrap CI: (${median_ci[0]:,.0f}, ${median_ci[1]:,.0f})")

# Exit rate CI (proportion)
exits = df['is_exited'].sum()
n_total = len(df)
p = exits / n_total
se_p = np.sqrt(p*(1-p)/n_total)
ci_p = (p - 1.96*se_p, p + 1.96*se_p)
print(f"\nOverall exit rate: {p*100:.2f}%, 95% CI: ({ci_p[0]*100:.2f}%, {ci_p[1]*100:.2f}%), n={n_total:,}")

# Multi-round vs single-round funding difference CI
multi = df[df['is_multi_round']]['funding_total_usd'].dropna()
single = df[~df['is_multi_round']]['funding_total_usd'].dropna()
diff = multi.mean() - single.mean()
se_diff = np.sqrt(multi.var()/len(multi) + single.var()/len(single))
ci_diff = (diff - 1.96*se_diff, diff + 1.96*se_diff)
print(f"\nMean funding difference (multi-round minus single-round): ${diff:,.0f}, 95% CI: (${ci_diff[0]:,.0f}, ${ci_diff[1]:,.0f})")

print("\n"+"="*80); print("2. HYPOTHESIS TESTS"); print("="*80)

print("\n--- Two-proportion z-test: US vs non-US exit rate ---")
us = df[df['country_code']=='USA']
non_us = df[df['country_code']!='USA']
count = np.array([us['is_exited'].sum(), non_us['is_exited'].sum()])
nobs = np.array([len(us), len(non_us)])
z_stat, p_val = proportions_ztest(count, nobs)
print(f"US exit rate: {us['is_exited'].mean()*100:.2f}% (n={len(us):,})")
print(f"Non-US exit rate: {non_us['is_exited'].mean()*100:.2f}% (n={len(non_us):,})")
print(f"z={z_stat:.2f}, p={p_val:.2e}")

print("\n--- Chi-square test: industry category (top 8) vs status ---")
top8 = df['primary_category'].value_counts().head(8).index
sub = df[df['primary_category'].isin(top8)]
ct = pd.crosstab(sub['primary_category'], sub['status'])
chi2, p_chi, dof, expected = stats.chi2_contingency(ct)
print(ct)
print(f"\nChi2={chi2:.2f}, dof={dof}, p={p_chi:.2e}")

print("\n--- One-way ANOVA + Tukey HSD post-hoc: funding by furthest_stage_category ---")
stage_df = df[['furthest_stage_category','funding_total_usd']].dropna()
stage_counts = stage_df['furthest_stage_category'].value_counts()
valid_stages = stage_counts[stage_counts >= 30].index
stage_df = stage_df[stage_df['furthest_stage_category'].isin(valid_stages)]
groups = [g['funding_total_usd'].values for _, g in stage_df.groupby('furthest_stage_category')]
f_stat, p_anova = stats.f_oneway(*groups)
print(f"ANOVA: F={f_stat:.2f}, p={p_anova:.2e}")
tukey = pairwise_tukeyhsd(stage_df['funding_total_usd'], stage_df['furthest_stage_category'], alpha=0.05)
print(tukey)

print("\n"+"="*80); print("3. REGRESSION MODEL + ASSUMPTION DIAGNOSTICS"); print("="*80)

# Predict log_funding_total_usd from engineered features + top industry dummies
model_df = df[['log_funding_total_usd','funding_rounds','years_since_founded',
               'is_multi_round','category_count','primary_category']].dropna()
top_industries = model_df['primary_category'].value_counts().head(6).index
model_df = model_df[model_df['primary_category'].isin(top_industries)].copy()
model_df['is_multi_round'] = model_df['is_multi_round'].astype(int)

formula = "log_funding_total_usd ~ funding_rounds + years_since_founded + is_multi_round + category_count + C(primary_category)"
model = smf.ols(formula, data=model_df).fit()
print(model.summary())

print("\n--- Assumption 1: Multicollinearity (VIF) ---")
X = model_df[['funding_rounds','years_since_founded','category_count']].copy()
X['is_multi_round'] = model_df['is_multi_round']
X = sm.add_constant(X)
vif_data = pd.DataFrame()
vif_data['feature'] = X.columns
vif_data['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif_data)

print("\n--- Assumption 2: Homoscedasticity (Breusch-Pagan test) ---")
bp_test = het_breuschpagan(model.resid, model.model.exog)
print(f"LM stat={bp_test[0]:.2f}, LM p-value={bp_test[1]:.2e}, F-stat={bp_test[2]:.2f}, F p-value={bp_test[3]:.2e}")
print("(p < 0.05 => evidence of heteroscedasticity; residual variance is not constant)")

print("\n--- Assumption 3: Normality of residuals (Shapiro-Wilk on a sample) ---")
resid_sample = np.random.choice(model.resid, size=min(5000, len(model.resid)), replace=False)
shapiro_stat, shapiro_p = stats.shapiro(resid_sample)
print(f"Shapiro-Wilk W={shapiro_stat:.4f}, p={shapiro_p:.2e}")

print(f"\nModel R-squared: {model.rsquared:.4f}, Adj R-squared: {model.rsquared_adj:.4f}")
print(f"N observations: {int(model.nobs):,}")

print("\nDONE")
