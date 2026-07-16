import warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import seaborn as sns
from scipy import stats

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 120

ROOT = Path(__file__).resolve().parents[2]
WH = str(ROOT / "data" / "warehouse") + "/"
OUT = str(ROOT / "docs" / "stats_charts") + "/"

fact = pd.read_csv(WH + "fact_startup_funding.csv", low_memory=False)
startup = pd.read_csv(WH + "dim_startup_with_source_key.csv", low_memory=False)
industry = pd.read_csv(WH + "dim_industry.csv", low_memory=False)
df = fact.merge(startup, on="startup_id").merge(industry, on="industry_id", how="left")

model_df = df[['log_funding_total_usd','funding_rounds','years_since_founded',
               'is_multi_round','category_count','primary_category']].dropna()
top_industries = model_df['primary_category'].value_counts().head(6).index
model_df = model_df[model_df['primary_category'].isin(top_industries)].copy()
model_df['is_multi_round'] = model_df['is_multi_round'].astype(int)
formula = "log_funding_total_usd ~ funding_rounds + years_since_founded + is_multi_round + category_count + C(primary_category)"
model = smf.ols(formula, data=model_df).fit()

fitted = model.fittedvalues
resid = model.resid

# 1. Residuals vs Fitted
fig, ax = plt.subplots(figsize=(8,6))
ax.scatter(fitted, resid, alpha=0.15, s=10, color='#1971C2')
ax.axhline(0, color='#E03131', linewidth=1.5)
ax.set_xlabel('Fitted values (log funding)')
ax.set_ylabel('Residuals')
ax.set_title('Residuals vs. Fitted Values\n(fan shape confirms Breusch-Pagan heteroscedasticity finding)')
plt.tight_layout(); plt.savefig(OUT+'01_residuals_vs_fitted.png'); plt.close()

# 2. Q-Q plot
fig, ax = plt.subplots(figsize=(7,7))
sm.qqplot(resid, line='45', ax=ax, markersize=3, alpha=0.3)
ax.set_title('Q-Q Plot of Residuals\n(deviation in tails confirms Shapiro-Wilk non-normality finding)')
plt.tight_layout(); plt.savefig(OUT+'02_qq_plot.png'); plt.close()

# 3. Distribution of funding_total_usd: raw vs log
fig, axes = plt.subplots(1,2, figsize=(12,5))
raw = df['funding_total_usd'].dropna()
axes[0].hist(raw[raw < raw.quantile(0.95)], bins=50, color='#1971C2')
axes[0].set_title('Raw funding_total_usd (95th pctile trimmed)\nHeavily right-skewed')
axes[1].hist(np.log1p(raw), bins=50, color='#2F9E44')
axes[1].set_title('log1p(funding_total_usd)\nMuch closer to normal -- justifies log target')
plt.tight_layout(); plt.savefig(OUT+'03_log_transform_justification.png'); plt.close()

print("Stats charts saved to", OUT)
