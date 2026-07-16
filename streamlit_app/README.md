# Streamlit App — Setup & Run

The online showcase companion to the project's Power BI dashboard. **Power BI remains the primary BI deliverable** — this app exists to make the project explorable in a browser (e.g. a portfolio link), with every number traceable back to the same validated pipeline.

## Run locally

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

### Optional: live PostgreSQL connection (SQL Insights page)

The app works fully without a database — SQL Insights falls back to an equivalent pandas computation automatically. To connect it to a real PostgreSQL instance instead, either:

- Set environment variables `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` (see `.env.example`), or
- Create `.streamlit/secrets.toml` with a `[postgres]` section (host, port, dbname, user, password) — the standard pattern for Streamlit Community Cloud deployments.

## All 10 pages (complete)

| Page | What it does |
|---|---|
| 🏠 Home | Hero, gradient KPI band, funding trend + top industries charts, nav grid |
| 📈 EDA | Live-filtered charts (4 tabs) + searchable/paginated table of all 101 written insights |
| 🧪 Statistics | Interactive confidence intervals, hypothesis tests (z-test/chi-square/ANOVA+Tukey), live regression diagnostics |
| 🗄️ SQL Insights | Real window-function queries, live DB or pandas fallback, materialized-view benchmark |
| 🤖 ML Predictions | Live funding + success prediction from the trained pipelines |
| 🔍 SHAP Explainability | Per-prediction waterfall charts + global feature importance |
| 🧭 Explorer | Startup/investor/country/industry search — AgGrid, filters, pagination, CSV export |
| 🏗️ Architecture | Interactive Sankey pipeline diagram + live self-diagnostic status panel |
| 📚 Documentation | All 8 written reports, cross-document search, per-doc and zip-all downloads |
| 👤 About | Project summary, build notes, GitHub/LinkedIn/résumé links |

## Architecture

```
streamlit_app/
├── app.py                  # entry point: page config, theme injection, st.navigation
├── .streamlit/config.toml  # base Streamlit theme hints
├── config/
│   ├── settings.py         # paths, constants, headline stats
│   └── theme.py            # dark/light design tokens + CSS
├── pages/                  # one render() function per page (10 pages)
├── components/
│   ├── icons.py            # inline SVG icon set (Lucide-style, no external dep)
│   ├── kpi_card.py         # gradient KPI card + skeleton loader
│   └── sidebar.py          # nav chrome, theme toggle, social links
├── utils/
│   ├── data_loader.py      # st.cache_data / st.cache_resource wrappers
│   ├── db_connector.py     # live PostgreSQL with graceful pandas fallback
│   ├── ml_predictor.py     # cached model loading + prediction
│   ├── shap_engine.py      # per-instance SHAP computation
│   ├── stats_engine.py     # cached hypothesis tests / regression diagnostics
│   ├── eda_parser.py       # parses eda_report.md into a searchable table
│   ├── docs_loader.py      # loads all written reports for the Documentation page
│   ├── sql_queries.py      # SQL + pandas-fallback pairs for SQL Insights
│   ├── error_handler.py    # @safe_run decorator, clean error UI
│   └── logger.py
├── assets/                 # resume.pdf goes here (see assets/README.md)
├── data/                   # copied from ../data/warehouse/ + ../docs/*.md
└── models/                 # copied from ../data/warehouse/*.pkl
```

## Before deploying

- Add a real `assets/resume.pdf` (both the sidebar and About page gracefully show a placeholder until then)
- Update `GITHUB_URL` and `LINKEDIN_URL` in `config/settings.py`
- Any host that runs `streamlit run app.py` works (Streamlit Community Cloud, Render, etc.)

## Testing

Every page in this app was validated with Streamlit's official `AppTest` framework (headless script execution) plus live-server smoke tests (`streamlit run` + `curl` health checks) before being considered done — not just visually spot-checked.

```python
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py")
at.run(timeout=30)
assert not at.exception
```
