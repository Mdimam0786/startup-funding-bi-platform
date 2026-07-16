"""
Parses docs/eda_report.md into a structured DataFrame (number, section, text)
so the EDA page can offer a searchable, filterable, paginated insights table
instead of a dumped wall of markdown.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR

REPORT_PATH = DATA_DIR / "reports" / "eda_report.md"

_SECTION_RE = re.compile(r"^##\s+(.+)$")
_INSIGHT_RE = re.compile(r"^(\d+)\.\s+(.+)$")


@st.cache_data(show_spinner=False)
def load_insights() -> pd.DataFrame:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(REPORT_PATH)

    text = REPORT_PATH.read_text(encoding="utf-8")
    rows = []
    current_section = "General"

    for line in text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        insight_match = _INSIGHT_RE.match(line.strip())
        if insight_match:
            number = int(insight_match.group(1))
            raw_text = insight_match.group(2).strip()
            # Strip markdown bold markers for clean display text, keep a
            # separate "highlight" flag for whether the insight has emphasis
            clean_text = raw_text.replace("**", "")
            rows.append({
                "number": number,
                "section": current_section,
                "insight": clean_text,
            })

    df = pd.DataFrame(rows).drop_duplicates(subset=["number"]).sort_values("number").reset_index(drop=True)
    return df
