"""
EDA computation script. Computes every statistic referenced in
docs/eda_report.md, against the actual warehouse tables. Nothing in the
report is hand-waved -- if a number appears in the report, it was
computed here first.
"""
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

WH = str(Path(__file__).resolve().parents[2] / "data" / "warehouse") + "/"

fact = pd.read_csv(WH + "fact_startup_funding.csv", low_memory=False)
startup = pd.read_csv(WH + "dim_startup_with_source_key.csv", low_memory=False)
geo = pd.read_csv(WH + "dim_geography.csv", low_memory=False)
industry = pd.read_csv(WH + "dim_industry.csv", low_memory=False)
date_dim = pd.read_csv(WH + "dim_date.csv", low_memory=False)
round_type = pd.read_csv(WH + "dim_round_type.csv", low_memory=False)
by_type = pd.read_csv(WH + "fact_funding_by_type.csv", low_memory=False)

# Denormalize once, for convenience (this is EDA, not the warehouse itself)
df = fact.merge(startup, on="startup_id").merge(geo, on="geography_id", how="left").merge(industry, on="industry_id", how="left")
df["founded_year"] = df["founded_date_id"].astype(str).str[:4].replace("nan", np.nan).astype(float)
df["first_funding_year"] = df["first_funding_date_id"].astype(str).str[:4].replace("nan", np.nan).astype(float)

print("="*80); print("SECTION 1: OVERALL SCALE"); print("="*80)
print(f"Total startups: {len(df):,}")
print(f"Total disclosed funding: ${df['funding_total_usd'].sum():,.0f}")
print(f"Startups with funding data: {df['funding_total_usd'].notna().sum():,} ({df['funding_total_usd'].notna().mean()*100:.1f}%)")
print(f"Median funding: ${df['funding_total_usd'].median():,.0f}")
print(f"Mean funding: ${df['funding_total_usd'].mean():,.0f}")
print(f"Countries represented: {df['country_code'].nunique()}")
print(f"Cities represented: {df['city'].nunique()}")
print(f"Industries (primary_category): {df['primary_category'].nunique()}")
print(f"Markets: {df['market'].nunique()}")
print(f"Unicorns matched: {df['is_unicorn'].sum()}")
print(f"Status breakdown:\n{df['status'].value_counts()}")

print("\n"+"="*80); print("SECTION 2: FUNDING TRENDS OVER TIME"); print("="*80)
yearly = df[df['first_funding_year'].between(1995,2015)].groupby('first_funding_year').agg(
    total_funding=('funding_total_usd','sum'), deals=('startup_id','count'), median_funding=('funding_total_usd','median')
).reset_index()
yearly['yoy_growth'] = yearly['total_funding'].pct_change()*100
print(yearly.to_string())
peak_year = yearly.loc[yearly['total_funding'].idxmax()]
print(f"\nPeak funding year: {peak_year['first_funding_year']:.0f} (${peak_year['total_funding']:,.0f})")
peak_deals_year = yearly.loc[yearly['deals'].idxmax()]
print(f"Peak deal-count year: {peak_deals_year['first_funding_year']:.0f} ({peak_deals_year['deals']:.0f} deals)")

print("\n"+"="*80); print("SECTION 3: INDUSTRY ANALYSIS"); print("="*80)
ind = df.groupby('primary_category').agg(
    startups=('startup_id','count'), total_funding=('funding_total_usd','sum'),
    median_funding=('funding_total_usd','median'), avg_funding=('funding_total_usd','mean'),
    exit_rate=('is_exited','mean'), unicorns=('is_unicorn','sum')
).query('startups >= 30').sort_values('total_funding', ascending=False)
print("Top 15 industries by total funding:")
print(ind.head(15).to_string())
print("\nTop 10 industries by median funding (min 30 startups):")
print(ind.sort_values('median_funding', ascending=False).head(10)[['startups','median_funding']].to_string())
print("\nTop 10 industries by exit rate (min 30 startups):")
print(ind.sort_values('exit_rate', ascending=False).head(10)[['startups','exit_rate']].to_string())
print(f"\nTotal distinct primary categories: {df['primary_category'].nunique()}")
print(f"Categories with >=30 startups: {len(ind)}")

print("\n"+"="*80); print("SECTION 4: GEOGRAPHIC / COUNTRY ANALYSIS"); print("="*80)
ctry = df.groupby('country_name').agg(
    startups=('startup_id','count'), total_funding=('funding_total_usd','sum'), unicorns=('is_unicorn','sum')
).sort_values('total_funding', ascending=False)
print("Top 15 countries by total funding:")
print(ctry.head(15).to_string())
top10_share = ctry.head(10)['total_funding'].sum() / ctry['total_funding'].sum() * 100
print(f"\nTop 10 countries = {top10_share:.1f}% of global disclosed funding")
us_share = ctry.loc['United States','total_funding'] / ctry['total_funding'].sum() * 100 if 'United States' in ctry.index else None
print(f"US share of global funding: {us_share:.1f}%")

print("\n"+"="*80); print("SECTION 5: CITY HUBS"); print("="*80)
city = df.groupby(['city','country_name']).agg(startups=('startup_id','count'), total_funding=('funding_total_usd','sum')).query('startups>=20').sort_values('total_funding',ascending=False)
print(city.head(15).to_string())

print("\n"+"="*80); print("SECTION 6: FUNDING STAGE / ROUND TYPE"); print("="*80)
print(df['furthest_stage_category'].value_counts(dropna=False))
print("\nAvg funding by furthest stage:")
print(df.groupby('furthest_stage_category')['funding_total_usd'].mean().sort_values(ascending=False))
rt = by_type.merge(round_type, on='round_type_id')
print("\nTotal amount by round type:")
print(rt.groupby('round_type_name')['amount_usd'].sum().sort_values(ascending=False).head(10))

print("\n"+"="*80); print("SECTION 7: SUCCESS / OUTCOME ANALYSIS"); print("="*80)
print(f"Overall exit rate (ipo+acquired): {df['is_exited'].mean()*100:.1f}%")
print(f"Overall closure rate: {df['is_closed'].mean()*100:.1f}%")
print(f"Median funding - exited companies: ${df[df['is_exited']]['funding_total_usd'].median():,.0f}")
print(f"Median funding - operating companies: ${df[df['status']=='operating']['funding_total_usd'].median():,.0f}")
print(f"Median funding - closed companies: ${df[df['is_closed']]['funding_total_usd'].median():,.0f}")
print(f"Median rounds - exited: {df[df['is_exited']]['funding_rounds'].median()}")
print(f"Median rounds - closed: {df[df['is_closed']]['funding_rounds'].median()}")
multi_round_exit = df.groupby('is_multi_round')['is_exited'].mean()*100
print(f"\nExit rate by multi-round status:\n{multi_round_exit}")

print("\n"+"="*80); print("SECTION 8: UNICORN ANALYSIS"); print("="*80)
uni = df[df['is_unicorn']]
print(f"Matched unicorns: {len(uni)}")
print(f"Unicorn countries (top 10):\n{uni['country_name'].value_counts().head(10)}")
print(f"Unicorn industries (top 10):\n{uni['primary_category'].value_counts().head(10)}")
print(f"Median years_since_founded for unicorns at last observed funding: {uni['years_since_founded'].median()}")
print(f"Median historical funding_total_usd for unicorns (in this old snapshot): ${uni['funding_total_usd'].median():,.0f}")

print("\n"+"="*80); print("SECTION 9: CORRELATION / STATISTICAL ANALYSIS"); print("="*80)
corr_cols = ['funding_total_usd','funding_rounds','years_since_founded','num_round_types_used','category_count']
corr_df = df[corr_cols].dropna()
print(corr_df.corr().round(3))

# ANOVA: does funding differ significantly by furthest_stage_category?
groups = [g['funding_total_usd'].dropna() for _, g in df.groupby('furthest_stage_category') if len(g)>30]
f_stat, p_val = stats.f_oneway(*groups)
print(f"\nANOVA (funding_total_usd by furthest_stage_category): F={f_stat:.2f}, p={p_val:.2e}")

# Correlation significance
r, p = stats.pearsonr(corr_df['funding_rounds'], corr_df['funding_total_usd'])
print(f"Pearson r (funding_rounds vs funding_total_usd): r={r:.3f}, p={p:.2e}")

r2, p2 = stats.pearsonr(corr_df['years_since_founded'], corr_df['funding_total_usd'])
print(f"Pearson r (years_since_founded vs funding_total_usd): r={r2:.3f}, p={p2:.2e}")

# t-test: multi-round vs single-round funding amounts
multi = df[df['is_multi_round']]['funding_total_usd'].dropna()
single = df[~df['is_multi_round']]['funding_total_usd'].dropna()
t_stat, p_t = stats.ttest_ind(multi, single, equal_var=False)
print(f"\nT-test (multi-round vs single-round funding): t={t_stat:.2f}, p={p_t:.2e}")
print(f"Multi-round median: ${multi.median():,.0f} | Single-round median: ${single.median():,.0f}")

print("\n"+"="*80); print("SECTION 10: COHORT / AGE ANALYSIS"); print("="*80)
df['founding_decade'] = (df['founded_year']//5*5)
decade = df[df['founding_decade'].between(1990,2014)].groupby('founding_decade').agg(
    startups=('startup_id','count'), median_funding=('funding_total_usd','median'), exit_rate=('is_exited','mean')
)
print(decade.to_string())

print("\nDONE")
