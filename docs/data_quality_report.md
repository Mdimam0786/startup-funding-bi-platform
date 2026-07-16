# Data Quality Report

Prepared by Md Imamuddin

This report summarizes the data quality checks performed on the raw and cleaned datasets used in the Startup Funding & Business Intelligence Platform.

## 1. Row Count Reconciliation

| Source | Raw Rows | Notes |
|---|---|---|
| investments_VC.csv | 54,294 | 4,856 fully-blank trailing rows removed |
| big_startup_secsees_dataset.csv | 66,368 | no blank/duplicate rows found |
| global_unicorn_companies.csv | 1,359 | retained as-is (2 industry data-entry fixes) |

**Merged `fact_funding_rounds_clean.csv`: 67,098 rows** (= investments_VC deduplicated ∩/∪ success_fail, per the merge strategy in the cleaning notes)

## 2. Completeness — Missing Values (Cleaned Fact Table)

| Column | % Missing |
|---|---|
| select_investors | 99.63% |
| valuation_billion_usd | 99.62% |
| unicorn_date_joined | 99.62% |
| valuation_tier | 99.62% |
| founded_month | 42.65% |
| founded_quarter | 42.65% |
| founded_year | 42.65% |
| state_code | 35.02% |
| market | 32.23% |
| seed | 26.32% |
| venture | 26.32% |
| equity_crowdfunding | 26.32% |
| undisclosed | 26.32% |
| convertible_note | 26.32% |
| debt_financing | 26.32% |
| angel | 26.32% |
| grant | 26.32% |
| private_equity | 26.32% |
| post_ipo_equity | 26.32% |
| post_ipo_debt | 26.32% |

(42 of 48 columns have any missing values; showing top 20 by missingness)

## 3. Validity Checks

- `funding_total_usd`: 53,652 non-null values, range $1 – $30,079,503,000, 0 values ≤ 0
- Duplicate `permalink` values in final fact table: 0
- `status` distribution: {'operating': 53727, 'closed': 6246, 'acquired': 5556, 'ipo': 1547, nan: 22}
- Rows flagged `is_pre_1900_founding` (kept, not dropped): 105
- Rows matched to unicorn list (`is_unicorn`=True): 254 of 1359 unicorns (18.7% match rate by exact name)
- Unicorn country → ISO3 mapping: 0 unmapped country name(s)

## 4. Known Limitations (documented, not hidden)

- **Unicorn match rate is exact (name, country) match only (~19%).** Many unicorns in the funding dataset likely exist under slightly different name formatting (e.g. punctuation, 'Inc'/'Ltd' suffixes, rebrands) or the Crunchbase snapshot simply predates their unicorn status (source data is pre-2015; most unicorns achieved that status later). A fuzzy-matching pass (e.g. `rapidfuzz`) could raise the match rate slightly, but the date mismatch is the bigger structural limitation — flagged here rather than hidden.
- **Crunchbase source data is historical** (funding activity concentrated pre-2015); all time-series analysis will be framed accordingly, not as "current market" data.
- **`category_list` is multi-valued** (pipe-delimited); we extract a `primary_category` (first listed) for simpler grouping, but this discards secondary categories — acceptable for headline industry analysis, revisit if sub-category drill-down is needed.
