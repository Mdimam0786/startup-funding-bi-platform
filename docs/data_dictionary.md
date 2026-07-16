# Data Dictionary — Star Schema

## Schema Diagram (logical)

```
                         ┌─────────────────┐
                         │   dim_date       │
                         │ (role-playing:   │
                         │  founded/first/  │
                         │  last funding)   │
                         └────────┬─────────┘
                                  │
┌──────────────┐         ┌───────▼────────────────┐         ┌──────────────┐
│ dim_geography│◄────────┤ fact_startup_funding     ├────────►│ dim_industry │
└──────────────┘         │ (grain: 1 row/startup)   │         └──────────────┘
                          └───────┬────────────────┘
                                  │ startup_id
                          ┌───────▼────────┐
                          │  dim_startup    │
                          └───────┬────────┘
                                  │ startup_id
                          ┌───────▼──────────────────┐
                          │ fact_funding_by_type       │
                          │ (grain: 1 row/startup/     │◄──── dim_round_type
                          │  round type; unpivoted)     │
                          └────────────────────────────┘
```

## Table: `dim_startup`
| Column | Type | Description |
|---|---|---|
| startup_id | INT PK | Surrogate key |
| permalink | VARCHAR | Natural key — Crunchbase org slug, traceable to source |
| name | VARCHAR | Company name |
| homepage_url | VARCHAR | Company website |
| status | VARCHAR | operating / closed / acquired / ipo |
| is_exited | BOOLEAN | status IN (ipo, acquired) |
| is_closed | BOOLEAN | status = closed |
| is_unicorn | BOOLEAN | Matched to the CB Insights unicorn list on (name, country) |
| valuation_billion_usd | NUMERIC | Only populated for matched unicorns |
| valuation_tier | VARCHAR | e.g. "$1-2B", "$50B+" — from unicorn source |
| category_count | SMALLINT | Number of categories the startup was tagged with in Crunchbase |
| is_pre_1900_founding | BOOLEAN | Data-quality flag — legitimate old institutions, exclude from "startup era" trend analysis if desired |

## Table: `dim_geography`
| Column | Type | Description |
|---|---|---|
| geography_id | INT PK | Surrogate key |
| country_code | CHAR(3) | ISO3 |
| country_name | VARCHAR | Resolved via pycountry |
| region | VARCHAR | Crunchbase "region" (metro-area granularity, not a continent) |
| state_code | VARCHAR | US state or equivalent, where applicable |
| city | VARCHAR | City |

## Table: `dim_industry`
| Column | Type | Description |
|---|---|---|
| industry_id | INT PK | Surrogate key |
| primary_category | VARCHAR | First category listed in Crunchbase's multi-value `category_list` |
| market | VARCHAR | Crunchbase's single-value "market" field (753 distinct values) |

## Table: `dim_round_type`
| Column | Type | Description |
|---|---|---|
| round_type_id | INT PK | Surrogate key |
| round_type_name | VARCHAR | e.g. seed, venture, round_A, debt_financing |
| stage_category | VARCHAR | Business grouping: Early Stage / Venture / Growth / Late Stage-Public / Debt / Alternative / Undisclosed |

## Table: `dim_date`
Standard calendar dimension, `date_id` = YYYYMMDD integer. Referenced three times (role-playing) by `fact_startup_funding` for founded/first-funding/last-funding dates.

## Table: `fact_startup_funding` (grain: one row per startup)
| Column | Description |
|---|---|
| funding_total_usd | Total disclosed funding raised |
| funding_rounds | Number of distinct funding rounds |
| years_since_founded | Age at analysis reference date (2015-01-01 — see note below) |
| days_to_first_funding | founded_at → first_funding_at, in days |
| funding_span_days | first_funding_at → last_funding_at, in days |
| avg_funding_per_round | funding_total_usd / funding_rounds |
| is_multi_round | funding_rounds > 1 |
| num_round_types_used | Count of distinct round-type columns with amount > 0 |
| has_debt_financing | Any debt_financing amount > 0 |
| log_funding_total_usd | log1p transform, for ML/statistical use |
| furthest_round_type / furthest_stage_category | The most advanced funding stage reached, derived by stage rank |

**Why the analysis reference date is 2015-01-01, not "today":** this Crunchbase snapshot's funding activity trails off around 2014–2015. Using today's date would make every startup look decades "older" and dormant than it was at the time the data was captured. All age/tenure features are anchored to the data's own timeframe.

## Table: `fact_funding_by_type` (grain: one row per startup per round type, only where amount > 0)
| Column | Description |
|---|---|
| startup_id | FK → dim_startup |
| round_type_id | FK → dim_round_type |
| amount_usd | Additive measure — safe to SUM across any dimension |

68,937 rows (vs. 67,098 startups × up to 21 possible round types) — confirms most startups only ever used 1–2 round types, consistent with `num_round_types_used` in the main fact.
