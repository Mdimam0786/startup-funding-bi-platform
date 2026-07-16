-- ============================================================
-- Startup Funding & Business Intelligence Platform
-- Developed by: Md Imamuddin
-- PostgreSQL Star Schema
-- ============================================================
-- ============================================================
-- Startup Funding & Business Intelligence Platform
-- Star Schema DDL (PostgreSQL 16)
-- ============================================================
-- Design notes:
--   - fact_startup_funding is the primary fact, grain = one row per startup.
--   - fact_funding_by_type is a second fact at grain = one row per
--     startup per round type, unpivoted from 21 wide source columns.
--     This shape is deliberate: it lets Power BI slice "funding by round
--     type" with a single additive measure instead of 21 near-duplicate
--     measures (a common anti-pattern seen in weaker portfolio projects).
--   - dim_date is a conformed, role-playing dimension: fact_startup_funding
--     references it three times (founded / first_funding / last_funding)
--     via three FK columns pointing at the same table.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS startup_bi;
SET search_path TO startup_bi;

-- ---------------- DIMENSIONS ----------------

CREATE TABLE dim_date (
    date_id     INTEGER PRIMARY KEY,        -- YYYYMMDD
    full_date   DATE NOT NULL,
    year        SMALLINT NOT NULL,
    quarter     SMALLINT NOT NULL,
    month       SMALLINT NOT NULL,
    month_name  VARCHAR(20) NOT NULL,
    day         SMALLINT NOT NULL,
    day_name    VARCHAR(20) NOT NULL
);

CREATE TABLE dim_geography (
    geography_id  SERIAL PRIMARY KEY,
    country_code  CHAR(3),
    country_name  VARCHAR(100),
    region        VARCHAR(150),
    state_code    VARCHAR(10),
    city          VARCHAR(150)
);
CREATE INDEX idx_dim_geography_country ON dim_geography(country_code);

CREATE TABLE dim_industry (
    industry_id       SERIAL PRIMARY KEY,
    primary_category  VARCHAR(200),
    market            VARCHAR(200)
);
CREATE INDEX idx_dim_industry_category ON dim_industry(primary_category);

CREATE TABLE dim_round_type (
    round_type_id   SERIAL PRIMARY KEY,
    round_type_name VARCHAR(50) NOT NULL UNIQUE,
    stage_category  VARCHAR(50)      -- Early Stage / Venture / Growth / Late Stage / Debt / Alternative
);

CREATE TABLE dim_startup (
    startup_id            SERIAL PRIMARY KEY,
    permalink             VARCHAR(255) UNIQUE,   -- natural key, traceable to Crunchbase source
    name                  VARCHAR(300),           -- 1 known source row has a missing name; kept, not dropped
    homepage_url          VARCHAR(500),
    status                VARCHAR(20),           -- operating / closed / acquired / ipo
    is_exited             BOOLEAN,
    is_closed             BOOLEAN,
    is_unicorn            BOOLEAN,
    valuation_billion_usd NUMERIC(10,2),
    valuation_tier        VARCHAR(20),
    category_count        SMALLINT,
    is_pre_1900_founding  BOOLEAN
);
CREATE INDEX idx_dim_startup_status ON dim_startup(status);
CREATE INDEX idx_dim_startup_unicorn ON dim_startup(is_unicorn);

-- ---------------- FACTS ----------------

CREATE TABLE fact_startup_funding (
    startup_id             INTEGER PRIMARY KEY REFERENCES dim_startup(startup_id),
    geography_id           INTEGER REFERENCES dim_geography(geography_id),
    industry_id            INTEGER REFERENCES dim_industry(industry_id),
    founded_date_id        INTEGER REFERENCES dim_date(date_id),
    first_funding_date_id  INTEGER REFERENCES dim_date(date_id),
    last_funding_date_id   INTEGER REFERENCES dim_date(date_id),
    funding_total_usd      NUMERIC(18,2),
    funding_rounds         SMALLINT,
    years_since_founded    NUMERIC(6,1),
    days_to_first_funding  NUMERIC(10,0),
    funding_span_days      NUMERIC(10,0),
    avg_funding_per_round  NUMERIC(18,2),
    is_multi_round         BOOLEAN,
    num_round_types_used   SMALLINT,
    has_debt_financing     BOOLEAN,
    log_funding_total_usd  NUMERIC(10,4),
    furthest_round_type    VARCHAR(50),
    furthest_stage_category VARCHAR(50)
);
CREATE INDEX idx_fact_startup_geo ON fact_startup_funding(geography_id);
CREATE INDEX idx_fact_startup_industry ON fact_startup_funding(industry_id);
CREATE INDEX idx_fact_startup_founded_date ON fact_startup_funding(founded_date_id);

CREATE TABLE fact_funding_by_type (
    startup_id      INTEGER REFERENCES dim_startup(startup_id),
    round_type_id   INTEGER REFERENCES dim_round_type(round_type_id),
    amount_usd      NUMERIC(18,2) NOT NULL,
    PRIMARY KEY (startup_id, round_type_id)
);
CREATE INDEX idx_fact_by_type_round ON fact_funding_by_type(round_type_id);

-- ---------------- EXAMPLE ANALYTICAL VIEW ----------------
-- A starter view Power BI/SQL analysts would query directly; more views
-- (materialized, with window functions) come in the SQL Analytics Layer phase.
CREATE OR REPLACE VIEW vw_startup_funding_overview AS
SELECT
    s.startup_id, s.name, s.status, s.is_unicorn, s.valuation_billion_usd,
    g.country_name, g.city,
    i.primary_category, i.market,
    f.funding_total_usd, f.funding_rounds, f.years_since_founded,
    f.furthest_stage_category
FROM fact_startup_funding f
JOIN dim_startup s   ON f.startup_id = s.startup_id
LEFT JOIN dim_geography g ON f.geography_id = g.geography_id
LEFT JOIN dim_industry i  ON f.industry_id = i.industry_id;
