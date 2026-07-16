# Statistical Analysis Report

I generated every result below with `src/stats/statistical_analysis.py`, run against the actual warehouse data — re-running that script reproduces every number here.

---

## 1. Confidence Intervals

| Metric | Point Estimate | 95% CI | n |
|---|---|---|---|
| Mean funding_total_usd | $15,534,229 | ($14,028,881 – $17,039,577) | 53,652 |
| Median funding_total_usd (bootstrap) | $1,750,000 | ($1,698,874 – $1,800,000) | 53,652 |
| Overall exit rate (IPO+acquired) | 10.59% | (10.35% – 10.82%) | 67,098 |
| Mean funding gap: multi-round vs. single-round | +$15,833,051 | ($12,213,783 – $19,452,319) | — |

**Business interpretation:** the mean's CI is nearly 10x wider (in relative terms) than the median's — a direct consequence of the extreme right-skew already flagged in the EDA report. The median's tight bootstrap CI ($1.70M–$1.80M) makes it the far more stable, trustworthy headline KPI for a dashboard; the mean should be reported alongside it but not as the sole number, since a handful of mega-rounds shift it substantially between resamples.

The multi-round funding gap's CI is entirely positive (doesn't cross zero) and fairly narrow relative to its size — strong evidence this isn't a fluke of the specific sample.

---

## 2. Hypothesis Tests

### 2.1 Two-proportion z-test — US vs. non-US exit rate
- US exit rate: **14.11%** (n=36,698) vs. non-US: **6.33%** (n=30,400)
- z = 32.60, **p < 0.001** (p = 4.5 × 10⁻²³³)

**Interpretation:** US-based startups exit at more than **2.2x** the rate of non-US startups, and this is about as statistically decisive a result as this dataset produces (the p-value is effectively zero). This isn't just "the US has more funding" (already shown) — even accounting for exit as a *rate*, not a raw count, US startups convert to IPO/acquisition far more often. Plausible drivers include a deeper, more liquid US M&A/IPO market rather than purely a funding-availability story — worth flagging as a hypothesis for further investigation rather than a proven causal mechanism.

### 2.2 Chi-square test of independence — Industry (top 8) × Status
- χ² = 903.21, dof = 21, **p < 0.001**

**Interpretation:** industry category and outcome status (operating/closed/acquired/ipo) are not independent — some industries produce meaningfully different outcome mixes than others. From the contingency table, **Biotechnology and Health Care show the highest IPO share relative to their size** (352 and 163 IPOs respectively, out of far fewer total companies than Software), while **Software shows the highest acquired-count (594)** — consistent with software being a frequent M&A target sector rather than an IPO-heavy one.

### 2.3 One-way ANOVA + Tukey HSD post-hoc — Funding by furthest_stage_category
- ANOVA: F = 150.14, **p < 0.001** (confirms an earlier EDA finding with a larger, cleaner subset)
- Tukey HSD (21 pairwise comparisons, family-wise error rate controlled at 0.05):
  - **17 of 21 pairs are statistically significant**; the 4 that are *not* significant are Alternative↔Early Stage, Alternative↔Undisclosed, Alternative↔Venture, and Undisclosed↔Venture
  - Every comparison involving **Late Stage/Public** is significant with large effect sizes (mean differences of $75M–$158M vs. every other stage)

**Business interpretation:** the ANOVA alone tells you stage matters; Tukey HSD tells you *which specific stage transitions* matter. The practical takeaway for a dashboard: **"Alternative," "Undisclosed," and "Venture" funding levels are not statistically distinguishable from each other** — grouping them together in a simplified view wouldn't lose real information, whereas collapsing "Growth" or "Late Stage/Public" into a broader bucket would hide a real, large, statistically robust difference.

---

## 3. Regression Model & Assumption Diagnostics

**Model:** `log_funding_total_usd ~ funding_rounds + years_since_founded + is_multi_round + category_count + C(primary_category)`, fit on the 6 largest industries (n = 9,973).

*(Log-transformed target — see diagnostic chart #3 for the justification: raw funding is heavily right-skewed, log1p is close to normal, which is a standard and necessary transform for OLS to be appropriate here.)*

### Key coefficients (all statistically significant except 3 industry dummies)
| Predictor | Coefficient | Interpretation |
|---|---|---|
| `is_multi_round` | +0.967 | Reaching a 2nd+ round is associated with **~163% higher** funding (e^0.967 − 1), holding other factors constant — the single largest effect in the model |
| `funding_rounds` | +0.403 | Each additional round is associated with **~50% more** total funding on average |
| `years_since_founded` | +0.078 | Each additional year of age associated with **~8% more** funding — small but significant |
| `category_count` | −0.108 | Each additional category tag associated with **~10% less** funding — companies tagged very broadly may read as less focused to investors, or reflect earlier-stage/less-defined companies |
| Biotechnology / Health Care dummies | +0.46 / +0.53 | Both significantly higher funding than the baseline category even after controlling for rounds/age — confirms an earlier EDA finding that these are capital-intensive sectors independent of company maturity |

**Model fit:** R² = 0.336 — the model explains about a third of the variance in log funding. This is a *reasonable*, not exceptional, fit — expected, since funding amount is also driven by unobservable factors (investor relationships, market timing, founder track record) that no dataset like this fully captures. This sets a realistic expectation for the ML regression model: don't expect R² much above ~0.35–0.45 without richer features.

### Assumption Diagnostics (checked, not assumed)

**1. Multicollinearity (VIF):** all VIFs are between 1.0 and 2.0 (well under the common threshold of 5) — no problematic multicollinearity among the numeric predictors. `funding_rounds` and `is_multi_round` have the highest VIFs (~1.96) since they're related by construction, but not enough to distort coefficient estimates.

**2. Homoscedasticity (Breusch-Pagan test):** LM p-value = 2.0×10⁻⁹⁵ — **the assumption is violated**; residual variance is not constant across fitted values. Visible directly in the residuals-vs-fitted plot (fan/funnel shape, wider spread at higher fitted values). **Practical implication:** the model's standard errors (and therefore its p-values) are somewhat unreliable as reported; a production version of this model should refit with heteroscedasticity-robust standard errors (`cov_type='HC3'` in statsmodels) before treating any single coefficient's p-value as precise — though the very large sample size and very small p-values on the main effects make it unlikely any of the headline conclusions above would flip.

**3. Normality of residuals (Shapiro-Wilk):** W = 0.984, p = 1.8×10⁻²³ — **technically violated**, visible in the Q-Q plot as tail deviation. With n≈10,000, Shapiro-Wilk is extremely sensitive to even small deviations from normality, so this is a common and expected result at this sample size — it does not by itself invalidate the model's practical use for prediction (OLS point estimates remain unbiased even under non-normal residuals; only exact small-sample inference is affected, and this sample is far from small).

**Bottom line on assumptions:** the model's coefficients and their signs/relative magnitudes are trustworthy and interpretable; the exact p-values and confidence intervals should be treated as approximate rather than precise, given the confirmed heteroscedasticity. This is the honest caveat a dashboard's "methodology" footnote should carry if this model's outputs are surfaced anywhere in Power BI.

---

## 4. Business Statistics Summary

1. **Report median, not mean, as the primary "typical funding" KPI** — its confidence interval is dramatically tighter and less sensitive to outlier mega-rounds.
2. **US vs. non-US exit-rate gap (14.1% vs 6.3%) is one of the most statistically robust findings in the entire analysis** (p ≈ 0) — a defensible, headline-worthy dashboard stat.
3. **Multi-round status is the single strongest funding predictor identified** (+163% associated funding) — more predictive in the regression than industry, age, or category breadth. This should be a top-priority engineered feature for the ML classifier/regressor.
4. **Funding-stage groupings can be simplified without losing statistical information**: Tukey HSD shows Alternative/Undisclosed/Venture aren't distinguishable from each other, but Growth and Late Stage/Public are distinct from everything — a 4-tier simplified stage variable (Early / Venture-and-similar / Growth / Late-Stage) would lose little real signal versus the current 7-category version, and would simplify a Power BI slicer considerably.
5. **Any regression or ML model built on this data should expect R² in the 0.3–0.45 range**, not higher — funding amount has a large unexplained component that structured company attributes alone can't capture. Setting this expectation now avoids over-promising in the ML write-up.
