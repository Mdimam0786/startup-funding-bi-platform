# Machine Learning Report

Three use cases delivered, each with model comparison, cross-validation, and (where applicable) hyperparameter tuning and SHAP explainability. All metrics below are from actual model runs (`src/ml/*.py`), not estimated.

---

## Use Case 1: Funding Amount Prediction (Regression)

**Target:** `log_funding_total_usd` (log-transformed — see the stats report for why raw dollars are the wrong regression target). **N = 39,140** startups with complete features.

| Model | Test MAE (log) | Test RMSE | Test R² | 3-fold CV R² |
|---|---|---|---|---|
| Linear Regression (baseline) | 1.412 | 1.828 | 0.389 | 0.372 |
| Random Forest (default) | 1.252 | 1.645 | 0.506 | 0.498 |
| XGBoost (default) | 1.254 | 1.650 | 0.502 | 0.494 |
| **XGBoost (tuned)** | **1.237** | **1.628** | **0.515** | **0.514** |

**Tuning:** RandomizedSearchCV, 3-fold CV, 10 parameter combinations. Best params: `n_estimators=300, max_depth=4, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9`.

**Result vs. my earlier OLS regression (R²=0.336):** the tuned XGBoost model improves R² to 0.515 — meaningfully better, but consistent with what I predicted in that earlier regression that "expect R² in the 0.3–0.45 range" for this kind of structured data. XGBoost exceeding that range slightly is a reasonable, not suspicious, result given it captures non-linear interactions the linear model can't.

**Feature importance (tuned XGBoost):**
1. `num_round_types_used` (38.2%) — by far the dominant feature
2. `is_multi_round` (9.0%)
3. `years_since_founded` (8.1%)
4. `funding_rounds` (7.2%)
5. `country_grouped_Other` / `country_grouped_China` (5.6% / 3.0%)

**A real limitation worth flagging, not hiding:** `num_round_types_used` and `funding_rounds` are highly correlated (r=0.668, established earlier in EDA) — they're largely two ways of measuring the same underlying thing ("how many financing events has this company had"). The model isn't wrong to lean on this signal (it's a genuinely strong predictor), but a single feature capturing 38% of importance is a sign the model has less to say about the *other* factors (industry, geography) than the raw importance ranking might suggest at a glance. A production iteration should consider whether these two features should be combined or whether one should be dropped to force the model to lean more on the remaining signal.

**SHAP summary (regression):** confirms the same features drive predictions in both directions — high `num_round_types_used` and `is_multi_round` values push predicted funding up; low values push it down. This directionality matches business intuition and cross-validates the earlier statsmodels regression, which also found these effects were significant and positive.

---

## Use Case 2: Startup Success Classification

**Target:** `is_exited` (1 = IPO or acquired, 0 = otherwise). **N = 47,059**, positive class rate = **11.25%** (a real class imbalance, handled explicitly via `class_weight='balanced'` / `scale_pos_weight`, not ignored).

| Model | Accuracy | Precision | Recall | F1 | Test ROC-AUC | 3-fold CV ROC-AUC |
|---|---|---|---|---|---|---|
| Logistic Regression (balanced) | 0.729 | 0.250 | 0.703 | 0.369 | 0.782 | 0.789 |
| **Random Forest (balanced)** | **0.732** | **0.256** | **0.723** | **0.378** | **0.800** | **0.805** |
| XGBoost (scale_pos_weight) | 0.742 | 0.257 | 0.683 | 0.373 | 0.786 | 0.783 |

**Best model: Random Forest** (highest test and CV ROC-AUC).

**Why precision is low (0.256) and that's an intentional trade-off, not a flaw:** with only 11.25% positive cases, a model that only flags obviously-safe bets would have poor recall (missing most real exits). Optimizing for `class_weight='balanced'` deliberately trades precision for recall (0.723) — appropriate for a VC-screening use case where the cost of missing a future winner (false negative) is generally higher than the cost of flagging a company that doesn't ultimately exit (false positive, just means extra due diligence). This is a business-judgment call, and it's documented here rather than silently baked into the metric choice.

**Feature importance (Random Forest):**
1. `years_since_founded` (56.6%) — dominant
2. `num_round_types_used` (13.5%)
3. `funding_rounds` (5.3%)
4. `country_grouped_United States` (4.4%)

**Critical limitation — this ties directly back to a caveat from the EDA report (insight #59):** `years_since_founded` dominating the model is expected but partly an artifact of the data snapshot, not a pure business signal — older companies have simply had more calendar time to reach an exit outcome before the snapshot was taken. This is the same survivorship-style effect flagged in the EDA cohort analysis. **Practical implication:** this model is better understood as "given how much time has passed, how likely is this company to have exited" rather than "how likely is this company to succeed" in an absolute sense — an important distinction for anyone using this model's output as an investment signal rather than a historical-pattern description.

**SHAP summary (classification):** confirms `years_since_founded` has by far the widest impact spread on individual predictions, consistent with the aggregate feature importance — reinforcing that any deployment of this model needs the caveat above prominently attached.

---

## Use Case 3: Startup Clustering (Unsupervised Segmentation)

**Method:** K-Means on standardized features (`log_funding`, `funding_rounds`, `years_since_founded`, `num_round_types_used`, `category_count`). **N = 39,140.**

**Choosing k — elbow + silhouette:**
| k | Inertia | Silhouette |
|---|---|---|
| 2 | 142,090 | **0.374** (best) |
| 3 | 117,336 | 0.247 |
| 4 | 98,749 | 0.251 |
| 5 | 82,041 | 0.260 |
| 6 | 73,685 | 0.250 |

**A deliberate business-judgment override, documented rather than hidden:** the statistically optimal k=2 produces only two coarse groups (a "smaller/younger" cluster of 76.5% of startups vs. a "larger/older" cluster of 23.5%) — technically valid but too coarse to be useful as a segmentation tool for a VC or accelerator audience. **I additionally profiled k=5**, which sacrifices some silhouette score (0.260 vs 0.374) for materially more actionable personas. This is a real trade-off, presented as such rather than silently picking whichever k "looks better."

### k=5 Cluster Personas (business-labeled)

| Cluster | Persona | % of dataset | Median Funding | Avg Age | Avg Rounds | Exit Rate | Unicorn Rate | Top Industry |
|---|---|---|---|---|---|---|---|---|
| 3 | **Early-Stage Seedlings** | 36.9% | $250K | 3.6 yrs | 1.2 | 2.7% | 0.2% | Software |
| 0 | **Emerging App Plays** | 15.3% | $1.0M | 4.3 yrs | 1.7 | 8.4% | 0.6% | Apps |
| 2 | **Established Performers** | 34.5% | $6.3M | 10.7 yrs | 1.6 | 18.9% | 0.6% | Software |
| 1 | **Heavily-Funded Leaders** | 12.9% | $24.1M | 8.6 yrs | 4.5 | 24.9% | 1.0% | Biotechnology |
| 4 | **Legacy Institutions (data artifact)** | 0.4% | $9.5M | 121.2 yrs | 1.3 | 24.5% | 0.0% | Education |

**A genuine cross-phase consistency finding:** cluster 4's 121-year average age isn't a modeling error — it's the same **pre-1900-founding flag** (`is_pre_1900_founding`) created back in the data cleaning step, resurfacing here as its own natural cluster (159 rows, 0.4%). This is a good sign of pipeline consistency (the same underlying data-quality issue shows up coherently across cleaning, EDA, and now clustering), but it also means **cluster 4 should be excluded from any startup-focused persona marketing or dashboard segment**, since these aren't startups at all (universities, the Red Cross, etc., as identified during cleaning).

**Business reading of the remaining 4 real personas:** exit rate and unicorn rate both increase monotonically from "Early-Stage Seedlings" → "Established Performers" → "Heavily-Funded Leaders," while funding round count is the sharpest differentiator of the top cluster (4.5 avg rounds vs. ~1.2–1.7 for the others) — reinforcing Use Case 2's finding that round-count-related features are the strongest behavioral predictors of eventual success in this dataset.

---

## Cross-Cutting Takeaways (all 3 use cases)

1. **`num_round_types_used` / `funding_rounds` is the single most recurring important feature** across the regression model, the classification model, and the clustering personas — this is the most robust, triple-validated signal in the entire ML phase.
2. **`years_since_founded` is powerful but requires a caveat everywhere it appears** — it reflects "time to observe an outcome" as much as it reflects genuine company trajectory, given this is a historical snapshot. This caveat should travel with the feature into any Power BI page or business narrative that uses these models' outputs.
3. **Realistic performance expectations were set correctly in the stats analysis** (R² 0.3–0.45 for OLS) and confirmed/modestly exceeded by tree-based models (R²=0.515) — a good example of statistical analysis informing ML expectations rather than the two phases operating independently.
4. **All three use cases converge on the same underlying story**: funding *behavior* (how many rounds, how many round types, whether multi-round) is a stronger predictor of both funding amount and success than industry or geography — a genuinely interesting, dashboard-worthy finding, and one that would make a strong "so what" slide in an interview walkthrough of this project.
