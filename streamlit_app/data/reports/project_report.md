# Project Report — Startup Funding & Business Intelligence Platform

## Overview

This project analyzes 67,098 real startups and $833.4B in disclosed funding, built as a complete analytics platform across 11 phases: planning, data sourcing, cleaning, schema design, database build, SQL analytics, EDA, statistics, ML, BI, and documentation. Every phase's output was validated before the next phase began — nothing in this report is asserted without a corresponding script that produced it.

## Data

Three real, public datasets (Crunchbase-derived funding data, a success/fail status dataset, and the CB Insights global unicorn list) were profiled, cleaned, and merged. Cleaning surfaced and fixed real issues: 4,856 fully-blank trailing rows, comma-formatted currency text, 6 corrupted future-dated years, and 108 legitimate pre-1900 institutions that needed flagging (not deleting). Final dataset: 67,098 startups with 0 duplicate permalinks.

## Data Model

A PostgreSQL star schema was built with two deliberately different fact-table grains: `fact_startup_funding` (one row per startup) and `fact_funding_by_type` (one row per startup per round type, unpivoted from 21 wide source columns specifically to support clean BI slicing). All foreign keys validated with zero orphans. Materialized views were benchmarked at a ~260x query speedup over live aggregation.

## Analysis

101 EDA insights and a formal statistical analysis (ANOVA, Tukey HSD, chi-square, regression with checked assumptions) established the dataset's core findings: extreme funding concentration in the US (72.6% of global total), a ~19x decline in median deal size from 2005–2014, and multi-round funding status as the strongest identified predictor of startup exit (2.1x higher exit rate, statistically significant at p<0.001).

## Machine Learning

Three ML use cases were built with model comparison, cross-validation, and hyperparameter tuning: funding regression (XGBoost, R²=0.515), success classification (Random Forest, ROC-AUC=0.800), and K-Means clustering (5 business-labeled personas). SHAP explainability was applied to both supervised models. All three converged on the same finding: funding *behavior* (round count, round-type diversity) outpredicts industry or geography.

## Business Intelligence

A 7-page Power BI dashboard was specified in full — data model, 43 DAX measures, and page-by-page visual specifications — including drill-through, bookmarks, field parameters, and what-if parameters. A genuine constraint (no Windows/Power BI Desktop access in this environment) is stated plainly rather than worked around; the specification is detailed enough to build the actual `.pbix` directly from it.

## Key Limitations (stated for transparency, not hidden)

- Source data is historical (1995–2015); no claims are made about current market conditions
- Unicorn matching is name+country exact match only (~19% match rate), limited primarily by the source data's date range predating most unicorns' actual valuation milestones
- Investor analysis is scoped to the 254 unicorn-matched startups only, since the broader dataset has no structured investor field
- Regression/classification models show honestly-reported statistical caveats (heteroscedasticity, non-normal residuals, a survivorship effect in the `years_since_founded` feature) rather than being presented as more reliable than they are

## Conclusion

This project demonstrates the complete analytics lifecycle on real data: not a single polished notebook, but a chain of validated, cross-referenced phases where each layer's assumptions and limitations are carried forward honestly rather than smoothed over for presentation.
