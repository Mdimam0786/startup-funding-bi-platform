# GitHub Publishing Checklist

## Before you push

- [ ] Rename the repo something specific and searchable: `startup-funding-bi-platform` (already matches folder name)
- [ ] Add a `LICENSE` file — MIT is the standard, low-friction choice for a portfolio project (`gh repo create` offers this, or add manually from choosealicense.com)
- [ ] Review `.gitignore` — by default it excludes `.env`, `__pycache__`, IDE files, and `.pbix`. Data files are currently **included** (commented-out exclusion) for a fully self-contained, runnable-on-clone portfolio repo. If the repo gets too large for comfortable cloning, uncomment the data exclusion lines and add a "Data" section to the README pointing to the Kaggle sources instead.
- [ ] Double-check no real credentials are committed — `config/config.yaml` intentionally has no password (env-var only); `.env.example` has a placeholder, not a real password
- [ ] Add topics/tags on GitHub: `data-engineering`, `postgresql`, `power-bi`, `machine-learning`, `python`, `sql`, `business-intelligence`, `data-science-portfolio`

## Repo description (for the GitHub "About" box)

> End-to-end BI platform analyzing $833B in real startup funding data — PostgreSQL star schema, statistical analysis, 3 ML models with SHAP, and a 43-measure Power BI dashboard spec.

## Suggested pinned/highlighted files for visitors

1. `README.md` (default landing page — already comprehensive)
2. `docs/eda_report.md` (101 insights — shows analytical depth fast)
3. `docs/ml_report.md` (shows ML rigor: model comparison, tuning, SHAP)
3. `powerbi/dashboard_specification.md` (shows BI/product thinking)

## What NOT to do

- Don't delete the `docs/data_quality_report.md` bug-fix narrative to "look cleaner" — documented bugs found and fixed is a strength in an interview, not a weakness to hide
- Don't remove the Power BI constraint disclosure — claiming a `.pbix` exists when it doesn't is the fastest way to lose credibility if asked to screen-share it
- Don't inflate metrics — every number in this repo is reproducible by running the corresponding script; keep it that way for any future edits

## Optional next steps (not required, but would strengthen the repo further)

- Build the actual `.pbix` from `powerbi/dashboard_specification.md` on a Windows machine with Power BI Desktop, then add real screenshots to `docs/` and link them from the README
- Add a `LICENSE` and a `CONTRIBUTING.md` if opening this to collaboration
- Set up a GitHub Actions workflow to re-run `src/eda/compute_eda_stats.py` on a schedule if the underlying data source ever gets refreshed
- Convert `docs/project_report.md` into a one-page PDF for easy attachment to job applications (the docx skill can help with this on request)
