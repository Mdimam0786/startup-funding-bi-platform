# Business Glossary

## Funding & Company Terms

**Funding Round** — A discrete event where a startup raises capital from investors. Multiple rounds over a company's life form its funding history.

**Funding Stage** — The maturity level implied by a round type. This project groups the 21 raw Crunchbase round types into 6 business-readable stage categories:
- **Early Stage**: seed, angel, convertible_note, equity_crowdfunding, product_crowdfunding
- **Venture**: venture, round_A
- **Growth**: round_B through round_H, private_equity
- **Late Stage / Public**: post_ipo_equity, post_ipo_debt, secondary_market
- **Debt**: debt_financing
- **Alternative**: grant, and other non-standard financing

**Exit** — A startup reaching IPO (going public) or being acquired by another company. In this project, `is_exited = TRUE` when `status IN ('ipo', 'acquired')`. Considered the primary "success" outcome for the classification model.

**Unicorn** — A privately-held startup valued at $1B or more. In this project, unicorn status comes from matching the CB Insights unicorn list to the funding dataset by (company name, country); only startups with an exact match carry `is_unicorn = TRUE`.

**Furthest Stage Reached** — The most advanced funding stage category a startup achieved, derived from its highest non-zero round-type column. Used as a single, simplified stage indicator instead of 21 separate flags.

**Multi-Round Startup** — A startup with `funding_rounds > 1`. Statistically the strongest predictor of exit likelihood identified in this project (16.6% exit rate vs. 8.0% for single-round startups).

## Data & Modeling Terms

**Star Schema** — A data warehouse design with a central fact table (measurements — e.g. funding amounts) surrounded by dimension tables (descriptive attributes — e.g. geography, industry). Chosen here for both query performance and direct compatibility with Power BI's modeling engine.

**Grain** — The level of detail one row in a fact table represents. This project uses two grains deliberately: `fact_startup_funding` (one row per startup) and `fact_funding_by_type` (one row per startup per round type) — see `docs/data_dictionary.md` for why both exist.

**Role-Playing Dimension** — A single dimension table referenced by a fact table in more than one way. `dim_date` plays three roles here (founded date, first funding date, last funding date) via three foreign keys, only one of which is "active" in Power BI by default.

**Materialized View** — A database query whose results are physically stored and periodically refreshed, rather than recomputed on every access. Used here (`mv_country_year_funding`, `mv_industry_summary`) for a measured ~260x query speedup versus live aggregation.

## Statistical Terms (as used in this project's reports)

**Confidence Interval (CI)** — A range that's likely to contain the true population value. This project consistently prefers reporting the median's CI over the mean's, since funding amounts are heavily right-skewed and the mean's CI is far wider/less stable.

**p-value** — The probability of observing a result this extreme if there were truly no effect. This project uses the conventional p < 0.05 threshold but reports exact p-values throughout rather than just "significant/not significant."

**Heteroscedasticity** — When a regression model's residual variance isn't constant across predictions (confirmed present in this project's OLS model via a Breusch-Pagan test) — means the model's point estimates are usable but its exact p-values/CIs are approximate, not precise.

**SHAP (SHapley Additive exPlanations)** — A method for attributing an ML model's individual predictions to its input features, based on cooperative game theory. Used here to explain both the regression and classification models' predictions, not just report aggregate feature importance.

## Project-Specific Caveats (glossary of "read this before you cite a number")

**Historical Snapshot** — This project's underlying data is a Crunchbase export with activity concentrated 1995–2015. Any "trend," "growth," or "current" language describes that window, not live market conditions.

**Survivorship / Time-to-Observe Effect** — Newer startup cohorts show lower exit rates not because they're performing worse, but because they've had less calendar time to reach an exit before the data snapshot was taken. This caveat applies to any cohort-based exit-rate comparison in this project.

**Legacy Institution Flag** (`is_pre_1900_founding`) — 108 rows in the dataset are real organizations (e.g., universities, the Red Cross) founded before 1900, not modern startups. Kept in the data (not silently dropped) but flagged, and excluded from startup-focused persona/cohort analysis.
