# Business Glossary

## Funding & Company Terms

**Funding Round** — A discrete event where a startup raises capital from investors. Multiple rounds over a company's life form its funding history.

**Funding Stage** — The maturity level implied by a round type. I grouped the 21 raw Crunchbase round types into 6 stage categories that are easier to talk about:
- **Early Stage**: seed, angel, convertible_note, equity_crowdfunding, product_crowdfunding
- **Venture**: venture, round_A
- **Growth**: round_B through round_H, private_equity
- **Late Stage / Public**: post_ipo_equity, post_ipo_debt, secondary_market
- **Debt**: debt_financing
- **Alternative**: grant, and other non-standard financing

**Exit** — A startup reaching IPO (going public) or being acquired by another company. I set `is_exited = TRUE` when `status IN ('ipo', 'acquired')`. This is the main "success" outcome the classification model predicts.

**Unicorn** — A privately-held startup valued at $1B or more. I get unicorn status by matching the CB Insights unicorn list to the funding dataset on (company name, country) — only startups with an exact match get `is_unicorn = TRUE`.

**Furthest Stage Reached** — The most advanced funding stage category a startup achieved, derived from its highest non-zero round-type column. Used as a single, simplified stage indicator instead of 21 separate flags.

**Multi-Round Startup** — A startup with `funding_rounds > 1`. This turned out to be the strongest predictor of exit likelihood I found (16.6% exit rate vs. 8.0% for single-round startups).

## Data & Modeling Terms

**Star Schema** — A data warehouse design with a central fact table (measurements — e.g. funding amounts) surrounded by dimension tables (descriptive attributes — e.g. geography, industry). I picked this for both query speed and because it maps cleanly onto Power BI's modeling engine.

**Grain** — The level of detail one row in a fact table represents. I deliberately used two different grains: `fact_startup_funding` (one row per startup) and `fact_funding_by_type` (one row per startup per round type) — see `docs/data_dictionary.md` for why both exist.

**Role-Playing Dimension** — A single dimension table referenced by a fact table in more than one way. In this project, `dim_date` plays three roles (founded date, first funding date, last funding date) through three foreign keys, and only one is "active" in Power BI by default.

**Materialized View** — A database query whose results are physically stored and periodically refreshed, rather than recomputed on every access. I used this for `mv_country_year_funding` and `mv_industry_summary`, and measured about a 260x query speedup over live aggregation.

## Statistical Terms (as used in this project's reports)

**Confidence Interval (CI)** — A range that's likely to contain the true population value. I stuck to reporting the median's CI instead of the mean's throughout, since funding amounts are heavily right-skewed and the mean's CI ends up much wider and less stable.

**p-value** — The probability of observing a result this extreme if there were truly no effect. I use the standard p < 0.05 threshold but report the exact p-value every time instead of just "significant" or "not significant."

**Heteroscedasticity** — When a regression model's residual variance isn't constant across predictions — I confirmed this is present in my OLS model with a Breusch-Pagan test, which means the point estimates are usable but the exact p-values and CIs are approximate, not precise.

**SHAP (SHapley Additive exPlanations)** — A method for attributing an ML model's individual predictions to its input features, based on cooperative game theory. I used this to explain individual predictions from both the regression and classification models, not just report aggregate feature importance.

## Project-Specific Caveats (glossary of "read this before you cite a number")

**Historical Snapshot** — The underlying data is a Crunchbase export with activity concentrated between 1995 and 2015. Any "trend," "growth," or "current" language in this project describes that window, not live market conditions.

**Survivorship / Time-to-Observe Effect** — Newer startup cohorts show lower exit rates not because they're performing worse, but because they've had less calendar time to reach an exit before the data snapshot was taken. This applies to any cohort-based exit-rate comparison I make in this project.

**Legacy Institution Flag** (`is_pre_1900_founding`) — 108 rows in the dataset are real organizations (e.g., universities, the Red Cross) founded before 1900, not modern startups. I kept these in the data instead of silently dropping them, flagged them, and excluded them from the startup-focused persona/cohort analysis.
