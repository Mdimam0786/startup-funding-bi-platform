"""
ETL Load: bulk-loads the star-schema CSVs (produced by transform.py) into
PostgreSQL, in FK-safe dependency order (dimensions before facts).

Uses psycopg2's COPY for speed -- appropriate for ~70K-row tables; a real
production pipeline at larger scale would consider COPY with a staging
table + upsert, but for this dataset size a straight COPY into empty
tables is the right amount of engineering.
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

log = get_logger("etl_load")

WAREHOUSE_DIR = Path(__file__).resolve().parents[2] / "data" / "warehouse"

DB_CONFIG = dict(
    host=os.environ.get("PGHOST", "localhost"),
    dbname=os.environ.get("PGDATABASE", "startup_bi_platform_updated"),
    user=os.environ.get("PGUSER", "mdimamuddin"),
    password=os.environ.get("PGPASSWORD", ""),
    port=os.environ.get("PGPORT", "5432"),
)

# Load order matters: dimensions must exist before facts reference them.
LOAD_ORDER = [
    ("dim_date.csv", "dim_date",
     ["date_id", "full_date", "year", "quarter", "month", "month_name", "day", "day_name"]),
    ("dim_geography.csv", "dim_geography",
     ["geography_id", "country_code", "country_name", "region", "state_code", "city"]),
    ("dim_industry.csv", "dim_industry",
     ["industry_id", "primary_category", "market"]),
    ("dim_round_type.csv", "dim_round_type",
     ["round_type_id", "round_type_name", "stage_category"]),
    ("dim_startup_with_source_key.csv", "dim_startup",
     ["permalink", "name", "homepage_url", "status", "is_exited", "is_closed",
      "is_unicorn", "valuation_billion_usd", "valuation_tier", "category_count",
      "is_pre_1900_founding", "startup_id"]),
    ("fact_startup_funding.csv", "fact_startup_funding",
     ["startup_id", "geography_id", "industry_id", "founded_date_id", "first_funding_date_id",
      "last_funding_date_id", "funding_total_usd", "funding_rounds", "years_since_founded",
      "days_to_first_funding", "funding_span_days", "avg_funding_per_round", "is_multi_round",
      "num_round_types_used", "has_debt_financing", "log_funding_total_usd",
      "furthest_round_type", "furthest_stage_category"]),
    ("fact_funding_by_type.csv", "fact_funding_by_type",
     ["startup_id", "round_type_id", "amount_usd"]),
]


def load_table(cur, csv_file, table_name, columns):
    path = WAREHOUSE_DIR / csv_file
    col_list = ", ".join(columns)
    with open(path, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"COPY startup_bi.{table_name} ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')",
            f,
        )
    log.info(f"  loaded {table_name} from {csv_file}")


def run():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        log.info("Truncating tables (idempotent reload) in reverse dependency order")
        for _, table_name, _ in reversed(LOAD_ORDER):
            cur.execute(f"TRUNCATE TABLE startup_bi.{table_name} CASCADE;")

        log.info("Loading tables in dependency order")
        for csv_file, table_name, columns in LOAD_ORDER:
            load_table(cur, csv_file, table_name, columns)

        conn.commit()
        log.info("ETL load committed successfully")
    except Exception as e:
        conn.rollback()
        log.error(f"ETL load failed, rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()
