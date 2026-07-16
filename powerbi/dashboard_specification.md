# Power BI Dashboard — Build Specification

## ⚠️ Important upfront constraint

Power BI Desktop is a Windows-only GUI application (.pbix is a proprietary binary format). This is a Linux sandbox, so I **cannot generate an actual .pbix file** — being upfront about that rather than claiming otherwise. What I've delivered instead is everything needed to build the real thing quickly and correctly:

1. **Data ready to import** — every warehouse CSV (`data/warehouse/*.csv`), already shaped as a proper star schema (see `docs/data_dictionary.md`), directly importable into Power BI's Get Data > Text/CSV, or connected live via PostgreSQL (Get Data > PostgreSQL database, using the credentials in `config.yaml`).
2. **43 DAX measures**, written and ready to paste (`dax_measures.dax`).
3. **This page-by-page specification** — detailed enough that building it in Power BI Desktop is a matter of following instructions, not making design decisions from scratch.

If you have access to Power BI Desktop, I'd estimate 3-4 hours of focused building to turn this spec into the actual .pbix. I'm glad to also just be a very detailed pair-programmer for that session if useful — happy to walk through each step interactively when you're at a Windows machine with Power BI installed.

---

## Data Model Setup (do this first)

1. Import all 9 warehouse tables: `dim_startup`, `dim_geography`, `dim_industry`, `dim_date`, `dim_round_type`, `dim_investor`, `fact_startup_funding`, `fact_funding_by_type`, `bridge_investor_unicorn`.
2. **Mark `dim_date` as a Date Table**: Model view → select `dim_date` → Table tools → Mark as date table → `full_date` column.
3. Relationships (all Many-to-One, single direction, from fact to dim):
   - `fact_startup_funding[geography_id]` → `dim_geography[geography_id]`
   - `fact_startup_funding[industry_id]` → `dim_industry[industry_id]`
   - `fact_startup_funding[startup_id]` → `dim_startup[startup_id]`
   - `fact_startup_funding[first_funding_date_id]` → `dim_date[date_id]` **(active)**
   - `fact_startup_funding[founded_date_id]` → `dim_date[date_id]` **(inactive — role-playing)**
   - `fact_startup_funding[last_funding_date_id]` → `dim_date[date_id]` **(inactive — role-playing)**
   - `fact_funding_by_type[startup_id]` → `dim_startup[startup_id]`
   - `fact_funding_by_type[round_type_id]` → `dim_round_type[round_type_id]`
   - `bridge_investor_unicorn[investor_id]` → `dim_investor[investor_id]`
   - `bridge_investor_unicorn[company]` → `dim_startup[name]` *(text join — flag as lower-confidence; a small number of name collisions are possible, same caveat as the unicorn-matching step)*
4. Paste all measures from `dax_measures.dax` into a dedicated **_Measures** table (Modeling → New Table → blank table used purely to organize measures, standard best practice).
5. Create the **Field Parameter** "Metric Selector" and **What-If Parameter** "Min Founding Year" referenced in the DAX file (Modeling ribbon → New parameter).

---

## Page 1: Executive Overview

**Purpose:** the page a recruiter or exec opens first — answers "how big is this market and is it healthy" in 10 seconds.

- **KPI card row (top):** Total Funding · Total Startups · Total Unicorns · Median Funding · Exit Rate % · Active Countries — each a Card visual bound to its measure, with `Funding YoY Growth %` shown as a small trend indicator beneath the Total Funding card (KPI visual, not just a plain card).
- **Center-left:** Combo chart — Total Funding (columns) + Total Startups (line) by `dim_date[year]`, replicating an earlier EDA chart but interactive.
- **Center-right:** Donut chart — funding share by `furthest_stage_category`.
- **Bottom:** Map visual (Azure Maps or standard Map) — bubble size = Total Funding, bubbles at `dim_geography[country_name]`.
- **Filters:** Year range slicer (dim_date), Country slicer, Industry slicer — all set to sync across every page (Format → Edit interactions, or use a shared filter pane).
- **Dynamic title:** bind the page title text box to `[Dynamic Title - Selected Country]`.

## Page 2: Funding Analytics

- **Top:** Line chart — `Total Funding` by Year/Quarter/Month, with a Year/Quarter/Month drill-down hierarchy built into `dim_date`.
- **Left:** Bar chart — `Total Funding` by `funding_rounds` bucket (create a calculated column bucketing 1, 2, 3, 4+ rounds).
- **Right:** Bar chart — Top 10 Funded Startups (`dim_startup[name]` by `Total Funding`, Top N filter = 10).
- **Bottom:** Stacked bar — `Funding by Round Type` (from `fact_funding_by_type`) by `dim_round_type[stage_category]`, sliced by year — this is the exact visual that justified unpivoting the fact table earlier on.
- **Tooltip page:** build a small tooltip-only page showing a startup's funding_total_usd, rounds, and stage, set as the custom tooltip for the Top 10 Startups bar chart (Format → Tooltip → Report page tooltip).

## Page 3: Industry Intelligence

- **Top-left:** Bar chart — Top 12 industries by `Total Funding` (matches EDA chart #2).
- **Top-right:** Scatter chart — X = `Total Startups` per industry, Y = `Exit Rate %` per industry, size = `Total Funding` — visually surfaces the "high volume, high exit rate" categories identified in the EDA report (Communications Hardware, Semiconductors).
- **Bottom:** Matrix visual — rows = `primary_category`, columns = `furthest_stage_category`, values = `Total Startups` — a funnel-by-industry cross-tab.
- **Drill-through:** right-click any industry bar → drill through to a dedicated "Industry Detail" page showing that industry's top startups, unicorns, and round-type mix.

## Page 4: Startup Intelligence

- **Top:** KPI cards — `Multi-Round Startup %`, `Avg Funding Rounds`, `Avg Years Since Founded`.
- **Left:** Funnel visual — startups by `furthest_stage_category` (Early Stage → Venture → Growth → Late Stage/Public), replicating EDA chart #4 as a true Power BI Funnel visual.
- **Right:** Bar chart — Exit Rate % by founding cohort (5-year buckets), replicating EDA chart #6, **with a text box explicitly noting the survivorship caveat from the EDA report (newer cohorts haven't had time to exit yet)** — this caveat needs to travel onto the dashboard, not stay buried in a report.
- **Bottom:** Table — status breakdown (operating/closed/acquired/ipo) with conditional formatting (data bars) on count.

## Page 5: Geographic Dashboard

- **Main:** Filled Map or ArcGIS map — countries shaded by `Total Funding`, using `dim_geography[country_name]`.
- **Side panel:** Ranked table — `Country Rank by Funding`, `Total Funding`, `Total Startups`, `Total Unicorns`, `Country % of Global Funding` — mirrors the SQL Pareto query directly.
- **Bottom:** Bar chart — Top 15 cities by `Total Funding` (matches EDA chart #3 style), with a note that this uses `City Rank by Funding`.
- **Bookmark:** create two bookmarks — "Country View" and "City View" — toggled by buttons, each showing/hiding the appropriate visual (Bookmark pane → Selected visuals option).

## Page 6: Investor Intelligence *(scope-limited — labeled honestly)*

**Important framing text box at the top of this page:** "Investor data is only available for the 254 startups matched to the global unicorn list (see the unicorn-matching methodology) — this page reflects unicorn-investor relationships, not the full 67K-startup dataset."

- **Top:** Bar chart — Top 15 investors by `Investor Portfolio Count` (Andreessen Horowitz, Accel, Sequoia Capital lead per the actual computed data).
- **Bottom:** Table — investor name, portfolio count, `Top Investor Rank`.
- This is intentionally a smaller, honestly-scoped page rather than a padded-out fake "full investor intelligence" page the data doesn't support.

## Page 7: Advanced Analytics (ML Outputs)

- **Top:** Table — `startup_clusters_k5.csv` persona summary (the 5 clusters from the ML phase), with a text box listing the 4 real personas + the 1 data-artifact cluster and why it's excluded from headline stats.
- **Middle:** Bar chart — feature importance from the regression and classification models (`regression_feature_importance.csv`, `classification_feature_importance.csv`) — imported as static reference tables since Power BI doesn't run Python models live in this setup.
- **Bottom:** Text box summarizing the 3 ML use cases' headline results (R²=0.515, ROC-AUC=0.800, 5 clusters) with a link/reference back to `ml_report.md` for full methodology — Power BI is for the story, not the full stats writeup.

---

## Cross-Page BI Features Checklist

| Feature | Where implemented |
|---|---|
| Drill-through | Industry Intelligence → Industry Detail page |
| Bookmarks | Geographic Dashboard (Country/City view toggle) |
| Dynamic tooltips | Funding Analytics (Top 10 Startups custom tooltip page) |
| Field Parameter | `Metric Selector` (used in `Dynamic Measure Selector` DAX measure) |
| What-If Parameter | `Min Founding Year` (used in `Startups Founded (What-If Year Threshold)`) |
| Dynamic titles | Executive Overview page title |
| Conditional formatting | Startup Intelligence status table (data bars), `KPI Status - Exit Rate` measure ready for font-color binding |
| Time intelligence | YoY, QoQ, rolling 12-month, CAGR — all in `dax_measures.dax` Section 2 |
| Role-playing dimension | `dim_date` used 3x via `USERELATIONSHIP` |

---

## Performance Notes

Import mode is recommended over DirectQuery given the dataset size (~67K rows is small for Power BI's Import engine, and the materialized views (`mv_country_year_funding`, `mv_industry_summary`) are already pre-aggregated — point Power BI at those for the Executive Overview page's KPI cards specifically, since that's measured to be ~260x faster than live aggregation.
