# Extra Charts — Supplementary Figures

These are additional figures generated during the notebook build (EDA, model building, evaluation, interpretation) that go beyond the curated set in `docs/eda_charts/`, `docs/ml_charts/`, and `docs/stats_charts/`. They're kept here for reference and traceability rather than mixed into the polished report folders.

## From `05_Exploratory_Data_Analysis.ipynb`

- `eda_notebook/01.png` — 2. Univariate analysis — distribution of funding amounts
- `eda_notebook/02.png` — 3. Univariate — categorical distributions (status, funding rounds count)
- `eda_notebook/03.png` — 4. Trend analysis — funding over time
- `eda_notebook/04.png` — Top 12 Industries by Total Disclosed Funding (min. 30 startups)
- `eda_notebook/05.png` — 4. Trend analysis — funding over time
- `eda_notebook/06.png` — Top 12 Countries by Total Disclosed Funding
- `eda_notebook/07.png` — Funding Stage Funnel: How Far Startups Get
- `eda_notebook/08.png` — Correlation Matrix: Funding & Engineered Features
- `eda_notebook/09.png` — Pairwise Relationships, colored by Exit Outcome (sample of 3,000)
- `eda_notebook/10.png` — Distribution of log(Funding) by Status
- `eda_notebook/11.png` — 10. Multivariate — pair plot across a sample
- `eda_notebook/12.png` — Exit Rate (IPO + Acquired) by Founding Cohort
- `eda_notebook/13.png` — Total Disclosed Amount by Round Type (Top 10)

## From `08_Statistical_Analysis.ipynb`

- `stats_notebook/01.png` — Observation & honest limitation

## From `09_Model_Building.ipynb`

- `model_building/01.png` — Hyperparameter tuning — RandomizedSearchCV on the best-performing live model

## From `10_Model_Evaluation.ipynb`

- `model_evaluation/01.png` — Regression metrics — full suite
- `model_evaluation/02.png` — Learning Curve — Regression Model
- `model_evaluation/03.png` — Confusion Matrix — Exit Prediction
- `model_evaluation/04.png` — Classification metrics — full suite
- `model_evaluation/05.png` — Calibration Curve
- `model_evaluation/06.png` — Precision / Recall / F1 vs. Decision Threshold

## From `11_Model_Interpretation.ipynb`

- `model_interpretation/01.png` — Permutation Importance — Regression Model
- `model_interpretation/02.png` — Permutation Importance — Classification Model
- `model_interpretation/03.png` — 1. Global interpretation — Permutation Importance (regression)
- `model_interpretation/04.png` — How to interpret a SHAP summary plot
- `model_interpretation/05.png` — Partial Dependence — Regression Model
- `model_interpretation/06.png` — ICE Plot + Partial Dependence Overlay — funding_rounds

## From `12_Final_Business_Insights.ipynb`

- `business_insights/01.png` — Why the Median is the Trustworthy KPI Here
- `business_insights/02.png` — Median Funding: Single- vs. Multi-Round Startups

