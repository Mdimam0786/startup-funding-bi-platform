"""
SQL query library for the SQL Insights page. Each entry pairs the real
SQL (window functions, CTEs -- reused from src/database/queries/business_queries.sql)
with a pandas-equivalent function, so the page works identically whether
or not a live PostgreSQL connection is available.
"""
import pandas as pd


QUERIES = {
    "top_funded_per_industry": {
        "label": "Top 5 Funded Startups per Industry (RANK)",
        "description": "Window function RANK() PARTITIONed by industry — powers a drill-through from an industry KPI to its leaders.",
        "sql": """SELECT * FROM (
    SELECT
        i.primary_category,
        s.name,
        f.funding_total_usd,
        RANK() OVER (PARTITION BY i.primary_category ORDER BY f.funding_total_usd DESC) AS rank_in_category
    FROM startup_bi.fact_startup_funding f
    JOIN startup_bi.dim_startup s ON f.startup_id = s.startup_id
    JOIN startup_bi.dim_industry i ON f.industry_id = i.industry_id
    WHERE f.funding_total_usd IS NOT NULL AND i.primary_category IS NOT NULL
) ranked
WHERE rank_in_category <= 5
ORDER BY primary_category, rank_in_category;""",
    },
    "yoy_growth": {
        "label": "Year-over-Year Funding Growth (LAG)",
        "description": "CTE pre-aggregates by year, then LAG() computes the prior-year comparison and growth %.",
        "sql": """WITH yearly_funding AS (
    SELECT d.year, SUM(f.funding_total_usd) AS total_funding, COUNT(*) AS deal_count
    FROM startup_bi.fact_startup_funding f
    JOIN startup_bi.dim_date d ON f.first_funding_date_id = d.date_id
    WHERE f.funding_total_usd IS NOT NULL
    GROUP BY d.year
)
SELECT
    year, total_funding, deal_count,
    LAG(total_funding) OVER (ORDER BY year) AS prior_year_funding,
    ROUND(
        (total_funding - LAG(total_funding) OVER (ORDER BY year))
        / NULLIF(LAG(total_funding) OVER (ORDER BY year), 0) * 100, 1
    ) AS yoy_growth_pct
FROM yearly_funding
ORDER BY year;""",
    },
    "country_pareto": {
        "label": "Country Funding Leaderboard with Cumulative % (Pareto)",
        "description": "Running SUM() OVER (ORDER BY ...) computes cumulative share of global funding — 'how many countries make up 80%?'",
        "sql": """WITH country_totals AS (
    SELECT g.country_name, SUM(f.funding_total_usd) AS total_funding
    FROM startup_bi.fact_startup_funding f
    JOIN startup_bi.dim_geography g ON f.geography_id = g.geography_id
    WHERE f.funding_total_usd IS NOT NULL AND g.country_name IS NOT NULL
    GROUP BY g.country_name
)
SELECT
    country_name,
    total_funding,
    RANK() OVER (ORDER BY total_funding DESC) AS country_rank,
    ROUND(total_funding / SUM(total_funding) OVER () * 100, 2) AS pct_of_global_funding,
    ROUND(
        SUM(total_funding) OVER (ORDER BY total_funding DESC)
        / SUM(total_funding) OVER () * 100, 2
    ) AS cumulative_pct_of_global_funding
FROM country_totals
ORDER BY total_funding DESC
LIMIT 20;""",
    },
    "funding_decile": {
        "label": "Funding Decile Bands (NTILE)",
        "description": "NTILE(10) splits startups into decile bands — a slicer-ready 'funding tier' without hardcoded dollar cutoffs.",
        "sql": """SELECT
    s.name,
    f.funding_total_usd,
    NTILE(10) OVER (ORDER BY f.funding_total_usd) AS funding_decile
FROM startup_bi.fact_startup_funding f
JOIN startup_bi.dim_startup s ON f.startup_id = s.startup_id
WHERE f.funding_total_usd IS NOT NULL
ORDER BY f.funding_total_usd DESC
LIMIT 25;""",
    },
}


# ---------------- Pandas fallbacks (used when no live DB connection) ----------------

def fallback_top_funded_per_industry(df: pd.DataFrame) -> pd.DataFrame:
    sub = df.dropna(subset=["funding_total_usd", "primary_category"]).copy()
    sub["rank_in_category"] = sub.groupby("primary_category")["funding_total_usd"].rank(method="min", ascending=False)
    top = sub[sub["rank_in_category"] <= 5].sort_values(["primary_category", "rank_in_category"])
    return top[["primary_category", "name", "funding_total_usd", "rank_in_category"]].reset_index(drop=True)


def fallback_yoy_growth(df: pd.DataFrame, date_dim: pd.DataFrame) -> pd.DataFrame:
    merged = df.merge(date_dim[["date_id", "year"]], left_on="first_funding_date_id", right_on="date_id", how="left")
    yearly = merged.dropna(subset=["funding_total_usd"]).groupby("year").agg(
        total_funding=("funding_total_usd", "sum"), deal_count=("startup_id", "count")
    ).reset_index()
    yearly["prior_year_funding"] = yearly["total_funding"].shift(1)
    yearly["yoy_growth_pct"] = ((yearly["total_funding"] - yearly["prior_year_funding"]) / yearly["prior_year_funding"] * 100).round(1)
    return yearly


def fallback_country_pareto(df: pd.DataFrame) -> pd.DataFrame:
    ctry = df.dropna(subset=["funding_total_usd", "country_name"]).groupby("country_name").agg(
        total_funding=("funding_total_usd", "sum")
    ).sort_values("total_funding", ascending=False).reset_index()
    ctry["country_rank"] = ctry["total_funding"].rank(method="min", ascending=False).astype(int)
    total = ctry["total_funding"].sum()
    ctry["pct_of_global_funding"] = (ctry["total_funding"] / total * 100).round(2)
    ctry["cumulative_pct_of_global_funding"] = ctry["pct_of_global_funding"].cumsum().round(2)
    return ctry.head(20)


def fallback_funding_decile(df: pd.DataFrame) -> pd.DataFrame:
    sub = df.dropna(subset=["funding_total_usd"]).copy().sort_values("funding_total_usd", ascending=False)
    sub["funding_decile"] = pd.qcut(sub["funding_total_usd"], 10, labels=False, duplicates="drop") + 1
    sub["funding_decile"] = 11 - sub["funding_decile"]
    return sub[["name", "funding_total_usd", "funding_decile"]].head(25).reset_index(drop=True)
