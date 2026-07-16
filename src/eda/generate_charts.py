import warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 120

ROOT = Path(__file__).resolve().parents[2]
WH = str(ROOT / "data" / "warehouse") + "/"
OUT = str(ROOT / "docs" / "eda_charts") + "/"

fact = pd.read_csv(WH + "fact_startup_funding.csv", low_memory=False)
startup = pd.read_csv(WH + "dim_startup_with_source_key.csv", low_memory=False)
geo = pd.read_csv(WH + "dim_geography.csv", low_memory=False)
industry = pd.read_csv(WH + "dim_industry.csv", low_memory=False)

df = fact.merge(startup, on="startup_id").merge(geo, on="geography_id", how="left").merge(industry, on="industry_id", how="left")
df["first_funding_year"] = df["first_funding_date_id"].astype(str).str[:4].replace("nan", np.nan).astype(float)

def money_fmt(x, pos):
    if x >= 1e9: return f'${x/1e9:.0f}B'
    if x >= 1e6: return f'${x/1e6:.0f}M'
    return f'${x:.0f}'

# 1. Funding trend over time
yearly = df[df['first_funding_year'].between(1998,2015)].groupby('first_funding_year').agg(
    total_funding=('funding_total_usd','sum'), deals=('startup_id','count')).reset_index()
fig, ax1 = plt.subplots(figsize=(10,5))
ax1.bar(yearly['first_funding_year'], yearly['total_funding'], color='#3B5BDB', alpha=0.85)
ax1.set_ylabel('Total Funding (USD)', color='#3B5BDB')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
ax2 = ax1.twinx()
ax2.plot(yearly['first_funding_year'], yearly['deals'], color='#F76707', marker='o', linewidth=2)
ax2.set_ylabel('Deal Count', color='#F76707')
ax1.set_title('Global Startup Funding: Total Amount vs. Deal Count by Year (1998–2015)')
ax1.set_xlabel('Year (first funding)')
plt.tight_layout(); plt.savefig(OUT+'01_funding_trend_over_time.png'); plt.close()

# 2. Top industries by total funding
ind = df.groupby('primary_category').agg(startups=('startup_id','count'), total_funding=('funding_total_usd','sum')).query('startups>=30').sort_values('total_funding',ascending=False).head(12)
fig, ax = plt.subplots(figsize=(10,6))
sns.barplot(y=ind.index, x=ind['total_funding'], ax=ax, palette='Blues_r')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
ax.set_title('Top 12 Industries by Total Disclosed Funding')
ax.set_xlabel('Total Funding'); ax.set_ylabel('')
plt.tight_layout(); plt.savefig(OUT+'02_top_industries_funding.png'); plt.close()

# 3. Top countries by total funding
ctry = df.groupby('country_name').agg(total_funding=('funding_total_usd','sum')).sort_values('total_funding',ascending=False).head(12)
fig, ax = plt.subplots(figsize=(10,6))
sns.barplot(y=ctry.index, x=ctry['total_funding'], ax=ax, palette='Greens_r')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
ax.set_title('Top 12 Countries by Total Disclosed Funding')
ax.set_xlabel('Total Funding'); ax.set_ylabel('')
plt.tight_layout(); plt.savefig(OUT+'03_top_countries_funding.png'); plt.close()

# 4. Funding stage funnel
stage_order = ['Early Stage','Venture','Growth','Late Stage / Public']
stage_counts = df['furthest_stage_category'].value_counts()
stage_counts = stage_counts.reindex(stage_order).dropna()
fig, ax = plt.subplots(figsize=(8,5))
bars = ax.barh(stage_order[::-1], [stage_counts.get(s,0) for s in stage_order[::-1]], color=['#1971C2','#1C7ED6','#4DABF7','#A5D8FF'][::-1])
ax.set_title('Funding Stage Funnel: How Far Startups Get')
ax.set_xlabel('Number of Startups')
for i,v in enumerate([stage_counts.get(s,0) for s in stage_order[::-1]]):
    ax.text(v, i, f' {int(v):,}', va='center')
plt.tight_layout(); plt.savefig(OUT+'04_funding_stage_funnel.png'); plt.close()

# 5. Correlation heatmap
corr_cols = ['funding_total_usd','funding_rounds','years_since_founded','num_round_types_used','category_count']
corr = df[corr_cols].dropna().corr()
fig, ax = plt.subplots(figsize=(7,6))
sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0, ax=ax, fmt='.2f', vmin=-0.3, vmax=0.3)
ax.set_title('Correlation Matrix: Funding & Engineered Features')
plt.tight_layout(); plt.savefig(OUT+'05_correlation_heatmap.png'); plt.close()

# 6. Cohort exit rate by founding decade
df['founding_decade'] = (df['founded_date_id'].astype(str).str[:4].replace('nan',np.nan).astype(float)//5*5)
decade = df[df['founding_decade'].between(1990,2014)].groupby('founding_decade').agg(exit_rate=('is_exited','mean')).reset_index()
fig, ax = plt.subplots(figsize=(9,5))
sns.barplot(x=decade['founding_decade'].astype(int).astype(str), y=decade['exit_rate']*100, ax=ax, color='#7048E8')
ax.set_title('Exit Rate (IPO + Acquired) by Founding Cohort')
ax.set_xlabel('Founding Cohort (5-year bucket)'); ax.set_ylabel('Exit Rate (%)')
plt.tight_layout(); plt.savefig(OUT+'06_exit_rate_by_cohort.png'); plt.close()

print("All 6 charts saved to", OUT)
