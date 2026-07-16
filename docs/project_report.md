# Project Report — Startup Funding & Business Intelligence Platform

## Overview

I built this project around 67,098 real startups and $833.4B in disclosed funding. I split the work into 11 phases: planning, data sourcing, cleaning, schema design, database build, SQL analytics, EDA, statistics, ML, BI, and documentation. I validated each phase's output before moving to the next one, so nothing in this report is a claim without a script behind it that actually produced it.

## Data

I profiled, cleaned, and merged three real, public datasets: Crunchbase-derived funding data, a success/fail status dataset, and the CB Insights global unicorn list. Cleaning turned up real problems I had to fix — 4,856 fully blank trailing rows, currency values stored as comma-formatted text, 6 rows with corrupted future-dated years, and 108 pre-1900 institutions that were legitimate and needed flagging rather than deleting. What I ended up with: 67,098 startups, 0 duplicate permalinks.

## Data model

I built a PostgreSQL star schema with two fact tables at deliberately different grains: `fact_startup_funding` (one row per startup) and `fact_funding_by_type` (one row per startup per round type — I unpivoted this from 21 wide source columns specifically so it would slice cleanly in BI). All foreign keys check out with zero orphans. I benchmarked the materialized views at roughly a 260x speedup over aggregating live.

## Analysis

I wrote up 101 EDA insights and ran a formal statistical analysis (ANOVA, Tukey HSD, chi-square, regression with the assumptions actually checked). The core findings: funding is heavily concentrated in the US (72.6% of the global total), median deal size fell about 19x from 2005 to 2014, and being multi-round is the strongest predictor I found for whether a startup exits (2.1x higher exit rate, p<0.001).

## Machine learning

I built three ML use cases, each with model comparison, cross-validation, and hyperparameter tuning: funding regression (XGBoost, R²=0.515), success classification (Random Forest, ROC-AUC=0.800), and K-Means clustering (5 personas I labeled by hand). I ran SHAP on both supervised models. All three point to the same thing: how a startup raises money (number of rounds, how varied the round types are) predicts more than its industry or location does.

## Business intelligence

I specified a 7-page Power BI dashboard in full — data model, 43 DAX measures, and page-by-page visual specs, including drill-through, bookmarks, field parameters, and what-if parameters. I don't have Windows or Power BI Desktop in this build environment, so I'm stating that limit plainly instead of faking around it. The spec is detailed enough that the actual `.pbix` can be built straight from it.

## Limitations I'm stating up front

- The source data is historical (1995–2015), so I'm not making any claims about current market conditions
- Unicorn matching is exact match on name + country only (~19% match rate) — this is mostly limited by the source data's date range predating when most unicorns actually hit their valuation milestones
- Investor analysis only covers the 254 unicorn-matched startups, because the broader dataset has no structured investor field
- The regression and classification models come with honestly reported caveats — heteroscedasticity, non-normal residuals, and a survivorship effect in the `years_since_founded` feature — rather than being presented as more solid than they actually are

## Conclusion

This project covers the full analytics lifecycle on real data — not one polished notebook, but a chain of validated phases where I carried each layer's assumptions and limits forward honestly instead of smoothing them over for the final presentation.
