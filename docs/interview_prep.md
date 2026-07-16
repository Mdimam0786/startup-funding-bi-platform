# Interview Preparation — Q&A

Real questions an interviewer would ask about this project, with answers grounded in what actually happened during the build (not generic talking points).

---

**Q: Walk me through this project.**

A: I built an end-to-end BI platform analyzing startup funding, using real Crunchbase and CB Insights data — 67,098 startups, $833.4B in disclosed funding. I went through the full stack deliberately, the way it'd be built at a company: profiled and cleaned the raw data, designed a star schema, loaded it into PostgreSQL, built a SQL analytics layer, ran EDA and formal statistical tests, built and compared 3 ML models, and specified a Power BI dashboard on top. Each phase's output fed the next — for example, a data-quality flag I created in cleaning (pre-1900 "startups" that were actually old institutions) resurfaced on its own as a distinct cluster in the ML phase, which was a nice confirmation the pipeline was internally consistent.

---

**Q: What was the hardest bug you ran into?**

A: Two stand out. First, a silent one: when I parsed the multi-value `category_list` field to get a primary industry, a naive split on the pipe delimiter returned empty strings for 77% of rows, because the source values had a *leading* pipe (`|Software|Mobile|`) I hadn't accounted for. It didn't error — it just quietly produced mostly-missing data, which is the worst kind of bug because nothing crashes. I caught it by checking the missingness rate after the transform and it looked implausibly high compared to the raw field's actual null rate.

Second: joining unicorn data onto the main fact table by company name alone silently duplicated rows, because names like "Bolt" or "Fabric" belong to genuinely different companies in different countries. I added an assertion (`row count before == row count after the merge`) specifically so that bug class can't reappear silently in the future.

---

**Q: Why PostgreSQL and a star schema instead of just working in pandas the whole time?**

A: Two reasons. Practically, a governed SQL layer is what Power BI expects to connect to, and it's what a BI team would actually build against — going straight from pandas to Power BI skips a layer real BI architecture has. Second, it forced better modeling discipline: I initially had round-type amounts as 20+ wide columns per startup, which is fine in a CSV but a bad shape for BI (you'd need 20 near-duplicate DAX measures to slice "funding by round type"). Designing for the star schema made me unpivot that into a proper narrow fact table early, which paid off later — Q8 in the SQL analytics layer and one of the Power BI pages both use that shape directly.

---

**Q: Your ML model only got R² = 0.515 for funding prediction. Isn't that low?**

A: It's actually roughly what I'd expect, and I said so before building the model — my earlier statistical regression (a simpler OLS model) got R²=0.336, and I explicitly wrote at the time that a real production model would likely land in the 0.3–0.45 range because funding amount is driven by a lot investors know (relationships, timing, founder reputation) that isn't in any dataset like this. The tree-based model modestly beating that range (0.515) makes sense since it captures non-linear interactions the OLS couldn't. I'd be more worried about an R² of 0.95 on this kind of data — that would suggest leakage, not skill.

---

**Q: How did you handle class imbalance in the success-classification model?**

A: Only 11.25% of startups exited, so I used `class_weight='balanced'` (and `scale_pos_weight` for XGBoost) rather than ignoring the imbalance. That's a real trade-off — it drops precision to about 0.26 in exchange for recall of 0.72. I made that trade-off deliberately: for a VC-style screening tool, missing a future winner (false negative) is generally more costly than flagging a company that doesn't pan out (false positive, just costs some extra diligence time). I documented that as a business judgment call in the report rather than just reporting the metric.

---

**Q: What's a limitation of this project you'd fix with more time?**

A: The unicorn match rate is low (~19%, name+country exact match) mostly because this Crunchbase snapshot predates when most companies in the unicorn list actually hit $1B valuations — the data just doesn't overlap much in time. A fuzzy-matching pass would help marginally, but the bigger fix would be sourcing a funding dataset with a later cutoff. I flagged this explicitly rather than quietly accepting a low match rate as final.

Separately, the regression model's top feature (`num_round_types_used`, 38% importance) is highly correlated with another top feature (`funding_rounds`, r=0.668) — I'd want to either combine them or drop one to see whether the model leans more on industry/geography signal without that redundancy.

---

**Q: How would you scale this if the dataset were 100x larger?**

A: A few things would need to change. The `COPY`-based ETL load works fine at 67K rows but I'd move to a staged load with upserts at real scale. I'd partition `fact_startup_funding` by year given how time-series-heavy the analysis is. The materialized views I built already point at the right pattern (pre-aggregate for BI performance) — I benchmarked a ~260x speedup from those at this scale, and that gap would only widen at 100x. For ML, I'd move from in-memory pandas to a sampling or Spark-based approach for feature engineering.

---

**Q: You didn't actually build the Power BI file — why?**

A: Honestly, because I built this in a Linux environment and Power BI Desktop is Windows-only with a proprietary binary format — I can't fake having built it. Rather than claim otherwise, I delivered everything needed to build it quickly and correctly: the star schema already exported and Power-BI-ready, all 43 DAX measures written and tested for logical correctness against the schema, and a page-by-page build spec detailed enough to follow literally. I'd rather be upfront about that gap than present something I didn't actually do.

---

**Q: What would you tell a stakeholder who wants to use your success-classification model to actually pick investments?**

A: I'd tell them not to use it that way without a caveat. The model's top feature, `years_since_founded`, is doing a lot of work — but it's partly an artifact of the data snapshot: older companies have simply had more calendar time to exit. The model is better understood as "given the time elapsed, how likely does this look like it exited" rather than a forward-looking success predictor. I'd rather surface that limitation clearly than let a model's ROC-AUC number imply more confidence than the underlying signal supports.

---

## Resume Bullet Points

- Built an end-to-end BI platform on 67K real-world startup funding records ($833.4B disclosed), covering data engineering, PostgreSQL/SQL, statistical analysis, ML, and Power BI
- Designed and implemented a PostgreSQL star schema with dual fact-table grains, reducing a 21-column wide funding breakdown into a query-efficient unpivoted structure; validated referential integrity with zero orphan foreign keys across 67K+ rows
- Built and benchmarked materialized views delivering a measured ~260x query speedup (32.9ms → 0.13ms) for BI-layer aggregations
- Conducted formal statistical analysis (ANOVA, Tukey HSD post-hoc, chi-square, Breusch-Pagan, Shapiro-Wilk) with explicit assumption diagnostics, not just descriptive statistics
- Trained and compared 3 ML use cases (regression, classification, clustering) with cross-validation, hyperparameter tuning, and SHAP explainability; best models achieved R²=0.515 and ROC-AUC=0.800
- Authored 43 production-ready DAX measures and a 7-page executive Power BI dashboard specification, including role-playing dimensions, drill-through, bookmarks, and field/what-if parameters
- Documented and fixed multiple real data-quality bugs (silent parsing failures, join fan-out duplication) with root-cause explanations, not just patched symptoms
