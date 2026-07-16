-- ============================================================
-- Startup Funding & Business Intelligence Platform
-- SQL Analytics Layer
-- Developed by: Md Imamuddin
-- ============================================================
-- ============================================================
-- Startup Funding & Business Intelligence Platform
-- SQL Analytics Layer
-- ============================================================
-- Every query below answers a specific business question from the
-- project brief. Each is annotated with intent, technique used, and
-- why that technique (not just "here's a window function").
-- ============================================================

SET search_path TO startup_bi;

-- ------------------------------------------------------------
-- Q1. Top 10 funded startups per industry (ranking within groups)
-- Technique: window function RANK() PARTITIONed by industry
-- Business use: "who are the category leaders" -- feeds a Power BI
-- drill-through page from an industry KPI card to its top companies.
-- ------------------------------------------------------------
SELECT * FROM (
    SELECT
        i.primary_category,
        s.name,
        f.funding_total_usd,
        RANK() OVER (PARTITION BY i.primary_category ORDER BY f.funding_total_usd DESC) AS rank_in_category
    FROM fact_startup_funding f
    JOIN dim_startup s ON f.startup_id = s.startup_id
    JOIN dim_industry i ON f.industry_id = i.industry_id
    WHERE f.funding_total_usd IS NOT NULL AND i.primary_category IS NOT NULL
) ranked
WHERE rank_in_category <= 10
ORDER BY primary_category, rank_in_category;


-- ------------------------------------------------------------
-- Q2. Year-over-year funding growth, global
-- Technique: CTE to pre-aggregate by year, then LAG() window function
-- for the prior-year comparison and growth %.
-- Business use: the single most important line on an Executive Overview
-- dashboard page.
-- ------------------------------------------------------------
WITH yearly_funding AS (
    SELECT d.year, SUM(f.funding_total_usd) AS total_funding, COUNT(*) AS deal_count
    FROM fact_startup_funding f
    JOIN dim_date d ON f.first_funding_date_id = d.date_id
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
ORDER BY year;


-- ------------------------------------------------------------
-- Q3. Country funding leaderboard with cumulative share of global total
-- Technique: window functions SUM() OVER (running total) and
-- SUM() OVER () (grand total) to compute a running "cumulative % of
-- global funding" -- the classic BI "how many countries make up 80% of
-- funding" (Pareto) question.
-- ------------------------------------------------------------
WITH country_totals AS (
    SELECT g.country_name, SUM(f.funding_total_usd) AS total_funding
    FROM fact_startup_funding f
    JOIN dim_geography g ON f.geography_id = g.geography_id
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
ORDER BY total_funding DESC;


-- ------------------------------------------------------------
-- Q4. Startup success rate by industry (minimum deal-count threshold)
-- Technique: CTE + conditional aggregation (FILTER clause)
-- Business use: "which industries have the best survival/exit odds" --
-- direct input to a VC investment-thesis narrative.
-- ------------------------------------------------------------
WITH industry_outcomes AS (
    SELECT
        i.primary_category,
        COUNT(*) AS total_startups,
        COUNT(*) FILTER (WHERE s.is_exited) AS exited_count,
        COUNT(*) FILTER (WHERE s.is_closed) AS closed_count
    FROM fact_startup_funding f
    JOIN dim_startup s ON f.startup_id = s.startup_id
    JOIN dim_industry i ON f.industry_id = i.industry_id
    WHERE i.primary_category IS NOT NULL
    GROUP BY i.primary_category
)
SELECT
    primary_category, total_startups, exited_count, closed_count,
    ROUND(exited_count::numeric / total_startups * 100, 1) AS exit_rate_pct,
    ROUND(closed_count::numeric / total_startups * 100, 1) AS closure_rate_pct
FROM industry_outcomes
WHERE total_startups >= 30   -- suppress noisy small-sample categories
ORDER BY exit_rate_pct DESC
LIMIT 20;


-- ------------------------------------------------------------
-- Q5. Funding percentile bands (NTILE) -- for a Power BI "funding tier"
-- slicer without hardcoding arbitrary dollar cutoffs.
-- ------------------------------------------------------------
SELECT
    s.name,
    f.funding_total_usd,
    NTILE(10) OVER (ORDER BY f.funding_total_usd) AS funding_decile
FROM fact_startup_funding f
JOIN dim_startup s ON f.startup_id = s.startup_id
WHERE f.funding_total_usd IS NOT NULL
ORDER BY f.funding_total_usd DESC
LIMIT 50;


-- ------------------------------------------------------------
-- Q6. City-level startup hub ranking (funding density, not just totals)
-- Technique: CTE + window function, normalizes by startup count so a
-- single mega-round doesn't make a small city look like a "hub".
-- ------------------------------------------------------------
WITH city_stats AS (
    SELECT
        g.city, g.country_name,
        COUNT(*) AS startup_count,
        SUM(f.funding_total_usd) AS total_funding,
        AVG(f.funding_total_usd) AS avg_funding_per_startup
    FROM fact_startup_funding f
    JOIN dim_geography g ON f.geography_id = g.geography_id
    WHERE g.city IS NOT NULL AND f.funding_total_usd IS NOT NULL
    GROUP BY g.city, g.country_name
    HAVING COUNT(*) >= 20
)
SELECT
    city, country_name, startup_count, total_funding, ROUND(avg_funding_per_startup, 0) AS avg_funding_per_startup,
    RANK() OVER (ORDER BY total_funding DESC) AS rank_by_total_funding,
    RANK() OVER (ORDER BY startup_count DESC) AS rank_by_startup_count
FROM city_stats
ORDER BY total_funding DESC
LIMIT 25;


-- ------------------------------------------------------------
-- Q7. Funding stage progression funnel
-- Technique: simple aggregation over the engineered furthest_stage_category
-- feature -- shows how far startups typically get, a classic VC funnel view.
-- ------------------------------------------------------------
SELECT
    furthest_stage_category,
    COUNT(*) AS startup_count,
    ROUND(AVG(funding_total_usd), 0) AS avg_total_funding,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_startups
FROM fact_startup_funding
WHERE furthest_stage_category IS NOT NULL
GROUP BY furthest_stage_category
ORDER BY avg_total_funding DESC NULLS LAST;


-- ------------------------------------------------------------
-- Q8. Round-type mix by industry (uses the unpivoted fact table)
-- Technique: joins the narrow fact_funding_by_type table -- this is
-- exactly the query shape that motivated unpivoting the fact table earlier; doing
-- this against the original 21-wide-column table would need 21 SUMs.
-- ------------------------------------------------------------
SELECT
    i.primary_category,
    rt.stage_category,
    SUM(fb.amount_usd) AS total_amount
FROM fact_funding_by_type fb
JOIN fact_startup_funding f ON fb.startup_id = f.startup_id
JOIN dim_industry i ON f.industry_id = i.industry_id
JOIN dim_round_type rt ON fb.round_type_id = rt.round_type_id
WHERE i.primary_category IS NOT NULL
GROUP BY i.primary_category, rt.stage_category
ORDER BY i.primary_category, total_amount DESC;


-- ============================================================
-- VIEWS (row-level, always live)
-- ============================================================

-- Unicorn scorecard -- joins startup + geography for a quick unicorn-only view
CREATE OR REPLACE VIEW vw_unicorn_scorecard AS
SELECT
    s.name, g.country_name, i.primary_category,
    s.valuation_billion_usd, s.valuation_tier, f.funding_total_usd, f.years_since_founded
FROM fact_startup_funding f
JOIN dim_startup s ON f.startup_id = s.startup_id
LEFT JOIN dim_geography g ON f.geography_id = g.geography_id
LEFT JOIN dim_industry i ON f.industry_id = i.industry_id
WHERE s.is_unicorn = TRUE;


-- ============================================================
-- MATERIALIZED VIEWS (pre-aggregated, refreshed on schedule)
-- These exist specifically to make Power BI Import-mode queries fast --
-- the dashboard should never force Power BI to aggregate 67K rows live
-- for a single KPI card.
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_country_year_funding AS
SELECT
    g.country_name, g.country_code, d.year,
    SUM(f.funding_total_usd) AS total_funding,
    COUNT(*) AS deal_count,
    COUNT(*) FILTER (WHERE s.is_unicorn) AS unicorn_count
FROM fact_startup_funding f
JOIN dim_geography g ON f.geography_id = g.geography_id
JOIN dim_date d ON f.first_funding_date_id = d.date_id
JOIN dim_startup s ON f.startup_id = s.startup_id
WHERE g.country_name IS NOT NULL
GROUP BY g.country_name, g.country_code, d.year;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_country_year ON mv_country_year_funding(country_name, year);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_industry_summary AS
SELECT
    i.primary_category,
    COUNT(*) AS startup_count,
    SUM(f.funding_total_usd) AS total_funding,
    AVG(f.funding_total_usd) AS avg_funding,
    COUNT(*) FILTER (WHERE s.is_exited) AS exited_count,
    COUNT(*) FILTER (WHERE s.is_unicorn) AS unicorn_count
FROM fact_startup_funding f
JOIN dim_industry i ON f.industry_id = i.industry_id
JOIN dim_startup s ON f.startup_id = s.startup_id
WHERE i.primary_category IS NOT NULL
GROUP BY i.primary_category;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_industry ON mv_industry_summary(primary_category);

-- Refresh procedure -- run after every ETL load
CREATE OR REPLACE PROCEDURE refresh_materialized_views()
LANGUAGE plpgsql
SET search_path = startup_bi
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_country_year_funding;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_industry_summary;
END;
$$;
