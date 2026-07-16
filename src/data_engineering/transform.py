"""
Transforms the cleaned, merged fact table into a proper star schema:
  - Surrogate-keyed dimension tables (dim_startup, dim_geography,
    dim_industry, dim_date, dim_round_type)
  - Two fact tables at two different, deliberate grains:
      fact_startup_funding   -> one row per startup (the main fact)
      fact_funding_by_type   -> one row per startup per round-type
                                 (unpivoted from the 20 wide round columns)

WHY two fact tables instead of one wide one:
The raw data stores round-type amounts (seed, venture, round_A...round_H,
etc.) as 20 separate columns on one row per startup. That's fine for a
flat CSV, but it's a bad shape for Power BI/DAX -- you can't easily slice
"total funding by round type" with a matrix or stacked bar without either
20 near-duplicate measures or an unpivot. So we unpivot here, once, in the
data layer, rather than making every dashboard page re-solve it in DAX.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

log = get_logger("transform")

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
WAREHOUSE_DIR = Path(__file__).resolve().parents[2] / "data" / "warehouse"

# Reference date for "years since founded" / "age" calculations.
# The source data is a historical Crunchbase snapshot (activity trails off
# ~2015), so we anchor to the last observed activity in the dataset rather
# than today's date -- using today's date would make every startup look
# artificially old/dormant.
ANALYSIS_REFERENCE_DATE = pd.Timestamp("2015-01-01")

ROUND_TYPE_COLUMNS = [
    "seed", "venture", "equity_crowdfunding", "undisclosed", "convertible_note",
    "debt_financing", "angel", "grant", "private_equity", "post_ipo_equity",
    "post_ipo_debt", "secondary_market", "product_crowdfunding",
    "round_A", "round_B", "round_C", "round_D", "round_E", "round_F", "round_G", "round_H",
]

# Groups round types into business-meaningful stage categories for
# dim_round_type -- useful for a "funding stage analysis" dashboard page
# without forcing the analyst to know what "post_ipo_debt" means.
ROUND_TYPE_CATEGORY = {
    "seed": "Early Stage", "angel": "Early Stage", "convertible_note": "Early Stage",
    "venture": "Venture", "round_A": "Venture", "round_B": "Venture", "round_C": "Venture",
    "round_D": "Growth", "round_E": "Growth", "round_F": "Growth", "round_G": "Growth", "round_H": "Growth",
    "private_equity": "Growth", "post_ipo_equity": "Late Stage / Public", "post_ipo_debt": "Late Stage / Public",
    "secondary_market": "Late Stage / Public", "debt_financing": "Debt",
    "equity_crowdfunding": "Alternative", "product_crowdfunding": "Alternative",
    "undisclosed": "Undisclosed", "grant": "Alternative",
}

# Highest-stage-reached ranking (higher number = later stage). Used to
# derive a single "furthest_funding_stage" feature per startup, which is
# often more useful for BI storytelling than 20 separate flag columns.
STAGE_RANK = {
    "grant": 1, "angel": 1, "seed": 1, "equity_crowdfunding": 1, "product_crowdfunding": 1, "convertible_note": 1,
    "venture": 2, "round_A": 2,
    "round_B": 3, "round_C": 4, "round_D": 5, "round_E": 6, "round_F": 7, "round_G": 8, "round_H": 9,
    "private_equity": 9, "debt_financing": 2, "undisclosed": 0,
    "post_ipo_equity": 10, "post_ipo_debt": 10, "secondary_market": 10,
}


def build_dim_date(fact: pd.DataFrame) -> pd.DataFrame:
    date_cols = ["founded_at", "first_funding_at", "last_funding_at"]
    all_dates = pd.concat([pd.to_datetime(fact[c], errors="coerce") for c in date_cols]).dropna().unique()
    dim = pd.DataFrame({"full_date": pd.to_datetime(sorted(all_dates))})
    dim["date_id"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["full_date"].dt.year
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["month"] = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.strftime("%B")
    dim["day"] = dim["full_date"].dt.day
    dim["day_name"] = dim["full_date"].dt.strftime("%A")
    dim = dim[["date_id", "full_date", "year", "quarter", "month", "month_name", "day", "day_name"]]
    log.info(f"dim_date built: {len(dim):,} unique dates")
    return dim


def build_dim_geography(fact: pd.DataFrame) -> pd.DataFrame:
    geo = fact[["country_code", "region", "state_code", "city"]].drop_duplicates().reset_index(drop=True)
    geo["geography_id"] = geo.index + 1

    try:
        import pycountry

        def country_name(code):
            try:
                return pycountry.countries.get(alpha_3=code).name if pd.notna(code) else None
            except Exception:
                return None

        geo["country_name"] = geo["country_code"].map(country_name)
    except ImportError:
        geo["country_name"] = None

    geo = geo[["geography_id", "country_code", "country_name", "region", "state_code", "city"]]
    log.info(f"dim_geography built: {len(geo):,} unique geography combinations")
    return geo


def build_dim_industry(fact: pd.DataFrame) -> pd.DataFrame:
    ind = fact[["primary_category", "market"]].drop_duplicates().reset_index(drop=True)
    ind["industry_id"] = ind.index + 1
    ind = ind[["industry_id", "primary_category", "market"]]
    log.info(f"dim_industry built: {len(ind):,} unique category/market combinations")
    return ind


def build_dim_round_type() -> pd.DataFrame:
    dim = pd.DataFrame({"round_type_name": ROUND_TYPE_COLUMNS})
    dim["round_type_id"] = dim.index + 1
    dim["stage_category"] = dim["round_type_name"].map(ROUND_TYPE_CATEGORY)
    dim = dim[["round_type_id", "round_type_name", "stage_category"]]
    log.info(f"dim_round_type built: {len(dim)} round types")
    return dim


def engineer_startup_features(fact: pd.DataFrame) -> pd.DataFrame:
    """Adds derived, business-meaningful columns to the startup grain."""
    df = fact.copy()

    founded = pd.to_datetime(df["founded_at"], errors="coerce")
    first_fund = pd.to_datetime(df["first_funding_at"], errors="coerce")
    last_fund = pd.to_datetime(df["last_funding_at"], errors="coerce")

    df["years_since_founded"] = ((ANALYSIS_REFERENCE_DATE - founded).dt.days / 365.25).round(1)
    # Guard against negative ages from any residual bad data
    df.loc[df["years_since_founded"] < 0, "years_since_founded"] = np.nan

    df["days_to_first_funding"] = (first_fund - founded).dt.days
    df["funding_span_days"] = (last_fund - first_fund).dt.days

    df["avg_funding_per_round"] = df["funding_total_usd"] / df["funding_rounds"].replace(0, np.nan)
    df["is_multi_round"] = df["funding_rounds"].fillna(0) > 1

    df["num_round_types_used"] = (df[ROUND_TYPE_COLUMNS] > 0).sum(axis=1)
    df["has_debt_financing"] = df["debt_financing"].fillna(0) > 0
    df["log_funding_total_usd"] = np.log1p(df["funding_total_usd"])

    # Furthest funding stage reached (business-readable, single column)
    def furthest_stage(row):
        used = [(col, STAGE_RANK.get(col, 0)) for col in ROUND_TYPE_COLUMNS if row[col] and row[col] > 0]
        if not used:
            return np.nan
        return max(used, key=lambda x: x[1])[0]

    df["furthest_round_type"] = df[ROUND_TYPE_COLUMNS].apply(furthest_stage, axis=1)
    df["furthest_stage_category"] = df["furthest_round_type"].map(ROUND_TYPE_CATEGORY)

    df["is_exited"] = df["status"].isin(["ipo", "acquired"])
    df["is_closed"] = df["status"] == "closed"

    log.info("Feature engineering complete: added 11 derived columns")
    return df


def unpivot_round_types(df: pd.DataFrame, dim_round_type: pd.DataFrame) -> pd.DataFrame:
    long_df = df.melt(
        id_vars=["permalink"],
        value_vars=ROUND_TYPE_COLUMNS,
        var_name="round_type_name",
        value_name="amount_usd",
    )
    long_df = long_df[long_df["amount_usd"].fillna(0) > 0]
    long_df = long_df.merge(dim_round_type[["round_type_id", "round_type_name"]], on="round_type_name", how="left")
    long_df = long_df[["permalink", "round_type_id", "amount_usd"]]
    log.info(f"fact_funding_by_type built: {len(long_df):,} rows (unpivoted from {len(ROUND_TYPE_COLUMNS)} wide columns)")
    return long_df


def run():
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    fact_raw = pd.read_csv(PROCESSED_DIR / "fact_funding_rounds_clean.csv", low_memory=False)

    fact_raw = engineer_startup_features(fact_raw)

    dim_date = build_dim_date(fact_raw)
    dim_geography = build_dim_geography(fact_raw)
    dim_industry = build_dim_industry(fact_raw)
    dim_round_type = build_dim_round_type()

    # dim_startup: one row per company, all descriptive/slowly-changing attributes
    dim_startup = fact_raw[[
        "permalink", "name", "homepage_url", "status", "is_exited", "is_closed",
        "is_unicorn", "valuation_billion_usd", "valuation_tier", "category_count",
        "is_pre_1900_founding",
    ]].drop_duplicates(subset=["permalink"]).reset_index(drop=True)
    dim_startup["startup_id"] = dim_startup.index + 1
    dim_startup["category_count"] = dim_startup["category_count"].astype("Int64")

    # fact_startup_funding: the main fact, one row per startup, FK'd to dims
    fact_startup_funding = fact_raw.merge(
        dim_geography, on=["country_code", "region", "state_code", "city"], how="left"
    ).merge(
        dim_industry, on=["primary_category", "market"], how="left"
    ).merge(
        dim_startup[["permalink", "startup_id"]], on="permalink", how="left"
    )

    def date_id_lookup(col):
        d = pd.to_datetime(fact_startup_funding[col], errors="coerce")
        return d.dt.strftime("%Y%m%d").where(d.notna()).astype("Int64")

    fact_startup_funding["founded_date_id"] = date_id_lookup("founded_at")
    fact_startup_funding["first_funding_date_id"] = date_id_lookup("first_funding_at")
    fact_startup_funding["last_funding_date_id"] = date_id_lookup("last_funding_at")
    fact_startup_funding["funding_rounds"] = fact_startup_funding["funding_rounds"].astype("Int64")

    fact_cols = [
        "startup_id", "geography_id", "industry_id",
        "founded_date_id", "first_funding_date_id", "last_funding_date_id",
        "funding_total_usd", "funding_rounds", "years_since_founded",
        "days_to_first_funding", "funding_span_days", "avg_funding_per_round",
        "is_multi_round", "num_round_types_used", "has_debt_financing",
        "log_funding_total_usd", "furthest_round_type", "furthest_stage_category",
    ]
    fact_startup_funding = fact_startup_funding[fact_cols]

    fact_funding_by_type = unpivot_round_types(fact_raw, dim_round_type)
    fact_funding_by_type = fact_funding_by_type.merge(
        dim_startup[["permalink", "startup_id"]], on="permalink", how="left"
    ).drop(columns=["permalink"])[["startup_id", "round_type_id", "amount_usd"]]

    # Persist warehouse tables
    dim_startup.drop(columns=["permalink"]).to_csv(WAREHOUSE_DIR / "dim_startup.csv", index=False,encoding="utf-8")
    # Keep permalink as a natural key reference table for traceability back to source
    dim_startup.to_csv(WAREHOUSE_DIR / "dim_startup_with_source_key.csv", index=False,encoding="utf-8")
    dim_geography.to_csv(WAREHOUSE_DIR / "dim_geography.csv", index=False,encoding="utf-8")
    dim_industry.to_csv(WAREHOUSE_DIR / "dim_industry.csv", index=False,encoding="utf-8")
    dim_date.to_csv(WAREHOUSE_DIR / "dim_date.csv", index=False,encoding="utf-8")
    dim_round_type.to_csv(WAREHOUSE_DIR / "dim_round_type.csv", index=False,encoding="utf-8")
    fact_startup_funding.to_csv(WAREHOUSE_DIR / "fact_startup_funding.csv", index=False,encoding="utf-8")
    fact_funding_by_type.to_csv(WAREHOUSE_DIR / "fact_funding_by_type.csv", index=False,encoding="utf-8")

    log.info(f"Star schema written to {WAREHOUSE_DIR}")
    for name, d in [
        ("dim_startup", dim_startup), ("dim_geography", dim_geography), ("dim_industry", dim_industry),
        ("dim_date", dim_date), ("dim_round_type", dim_round_type),
        ("fact_startup_funding", fact_startup_funding), ("fact_funding_by_type", fact_funding_by_type),
    ]:
        log.info(f"  {name}: {len(d):,} rows x {d.shape[1]} cols")


if __name__ == "__main__":
    run()
