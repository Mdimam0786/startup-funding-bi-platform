"""
Database connector with graceful degradation. This app may run somewhere
without access to the project's PostgreSQL instance (e.g. Streamlit
Community Cloud with no DB configured) -- rather than crash, every query
on the SQL Insights page falls back to an equivalent pandas computation
on the same underlying CSVs, clearly labeled as such. Connection details
come from st.secrets first (the standard Streamlit deployment pattern),
then environment variables, matching src/database/etl_load.py's approach.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.logger import get_logger

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

log = get_logger("db_connector")


def _get_db_config() -> dict:
    try:
        secrets = st.secrets.get("postgres", {})
    except Exception:
        secrets = {}
    return {
        "host": secrets.get("host") or os.environ.get("PGHOST", "localhost"),
        "dbname": secrets.get("dbname") or os.environ.get("PGDATABASE", "startup_bi_platform_updated"),
        "user": secrets.get("user") or os.environ.get("PGUSER", "mdimamuddin"),
        "password": secrets.get("password") or os.environ.get("PGPASSWORD", ""),
        "port": secrets.get("port") or os.environ.get("PGPORT", "5432"),
    }


@st.cache_resource(show_spinner=False)
def get_connection():
    """Returns a live psycopg2 connection, or None if unavailable. Never raises."""
    try:
        import psycopg2
        config = _get_db_config()
        conn = psycopg2.connect(connect_timeout=3, **config)
        log.info("Live PostgreSQL connection established.")
        return conn
    except Exception as e:
        log.info(f"No live PostgreSQL connection available, will use pandas fallback: {e}")
        return None


def is_live() -> bool:
    return get_connection() is not None


@st.cache_data(show_spinner=False, ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    """Runs SQL against the live connection. Raises if no connection --
    callers should check is_live() first and use a fallback if False."""
    conn = get_connection()
    if conn is None:
        raise ConnectionError("No live database connection available.")
    return pd.read_sql_query(sql, conn)


@st.cache_data(show_spinner=False, ttl=600)
def explain_analyze_timing(sql: str) -> float:
    """Runs EXPLAIN ANALYZE and extracts the actual execution time in ms."""
    conn = get_connection()
    if conn is None:
        raise ConnectionError("No live database connection available.")
    cur = conn.cursor()
    cur.execute(f"EXPLAIN ANALYZE {sql}")
    rows = cur.fetchall()
    cur.close()
    for row in rows:
        text = row[0]
        if "Execution Time" in text:
            return float(text.split(":")[1].strip().replace(" ms", ""))
    return -1.0
