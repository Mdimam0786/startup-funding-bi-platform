"""
Cached loader for the project's written documentation. Each entry maps a
key to metadata (title, icon, short description) plus the raw markdown
content, so the Documentation page can list, search, and render any of
them without re-reading files on every rerun.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR

REPORTS_DIR = DATA_DIR / "reports"

DOC_REGISTRY = {
    "project_report": {
        "title": "Project Report", "icon": "📋",
        "description": "End-to-end narrative summary of all 11 project phases.",
        "file": "project_report.md",
    },
    "data_dictionary": {
        "title": "Data Dictionary", "icon": "🗂️",
        "description": "Full star schema reference — every table and column defined.",
        "file": "data_dictionary.md",
    },
    "business_glossary": {
        "title": "Business Glossary", "icon": "📖",
        "description": "Domain terms, modeling terms, and every caveat worth citing correctly.",
        "file": "business_glossary.md",
    },
    "data_quality_report": {
        "title": "Data Quality Report", "icon": "🔍",
        "description": "Before/after cleaning metrics — real bugs found and fixed.",
        "file": "data_quality_report.md",
    },
    "eda_report": {
        "title": "EDA Report", "icon": "📈",
        "description": "101 numbered insights, each traced to a computed statistic.",
        "file": "eda_report.md",
    },
    "statistical_analysis_report": {
        "title": "Statistical Analysis", "icon": "🧪",
        "description": "Confidence intervals, hypothesis tests, regression diagnostics.",
        "file": "statistical_analysis_report.md",
    },
    "ml_report": {
        "title": "ML Report", "icon": "🤖",
        "description": "Model comparisons, tuning, SHAP, and clustering personas.",
        "file": "ml_report.md",
    },
    "interview_prep": {
        "title": "Interview Prep", "icon": "💬",
        "description": "Real Q&A grounded in this project's actual decisions and bugs.",
        "file": "interview_prep.md",
    },
}


@st.cache_data(show_spinner=False)
def load_all_docs() -> dict:
    docs = {}
    for key, meta in DOC_REGISTRY.items():
        path = REPORTS_DIR / meta["file"]
        content = path.read_text(encoding="utf-8") if path.exists() else f"*{meta['file']} not found.*"
        docs[key] = {**meta, "content": content}
    return docs


def search_docs(docs: dict, query: str) -> list:
    """Returns list of (key, doc, matching_lines) for docs containing query."""
    if not query:
        return []
    query_lower = query.lower()
    results = []
    for key, doc in docs.items():
        lines = doc["content"].splitlines()
        matches = [line.strip() for line in lines if query_lower in line.lower() and line.strip()]
        if matches:
            results.append((key, doc, matches[:3]))
    return results
