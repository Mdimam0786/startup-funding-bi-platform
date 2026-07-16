"""
Data cleaning module.

Cleans and standardizes the three raw source files:
  1. investments_VC.csv          -> base of fact_funding_rounds (round-level detail)
  2. big_startup_secsees_dataset.csv -> supplies clean status labels + fills gaps
  3. global_unicorn_companies.csv     -> supplies unicorn flag / valuation

Every transformation implemented in this module is based on issues
identified during the exploratory data profiling and validation process.
The resulting data quality report documents the final cleaned dataset.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

log = get_logger("clean")

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
INTERIM_DIR = Path(__file__).resolve().parents[2] / "data" / "interim"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

# Reasonable bounds for a "startup founded/funded" date. Anything outside
# this is either a pre-modern-startup-era organization (e.g. universities,
# the Red Cross) or a data-entry typo (e.g. year 2914).
MIN_VALID_YEAR = 1900
MAX_VALID_YEAR = 2025

# Manual overrides for country names that pycountry/fuzzy matching gets wrong
# or that don't have a clean ISO3 mapping out of the box.
COUNTRY_NAME_TO_ISO3_OVERRIDES = {
    "United States": "USA",
    "United Kingdom": "GBR",
    "South Korea": "KOR",
    "Vietnam": "VNM",
    "Russia": "RUS",
    "Bahamas": "BHS",
    "Czech Republic": "CZE",
    "Ivory Coast": "CIV",
    "Democratic Republic of the Congo": "COD",
    "United Arab Emirates": "ARE",
    "Turkey": "TUR",
}

# Known data-entry error corrections in the unicorn dataset's `industry`
# column (city/generic terms found sitting where an industry should be).
UNICORN_INDUSTRY_FIXES = {
    "Vultr": "Enterprise Tech",   # cloud infrastructure company
    "MindMaze": "Healthcare & Life Sciences",  # neurotech/health company
}


def clean_currency_string(series: pd.Series) -> pd.Series:
    """
    Cleans currency-formatted text columns like ' 17,50,000 ' or ' -   '
    into proper floats. Handles comma-grouping (including Indian-style
    lakh grouping, which doesn't affect digit order) and treats a lone
    '-' as missing/zero -> NaN.
    """
    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.replace({"-": None, "nan": None, "": None})
    cleaned = cleaned.str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def null_out_impossible_years(df: pd.DataFrame, date_cols: list, min_year=MIN_VALID_YEAR, max_year=None) -> pd.DataFrame:
    """
    Nulls out dates whose year is an obvious typo (e.g. 2105, 2914).
    Does NOT drop pre-1900 rows -- those are flagged separately since they
    may be legitimate (old institutions), not necessarily wrong.
    """
    df = df.copy()
    for col in date_cols:
        parsed = pd.to_datetime(df[col], errors="coerce")
        year = parsed.dt.year
        bad_future = year > (max_year if max_year else pd.Timestamp.now().year + 1)
        n_bad = bad_future.sum()
        if n_bad:
            log.info(f"  nulling {n_bad} impossible future-dated values in '{col}'")
        df.loc[bad_future, col] = pd.NaT
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_investments_vc() -> pd.DataFrame:
    log.info("Loading investments_VC.csv (latin1 encoding)")
    df = pd.read_csv(RAW_DIR / "investments_VC.csv", encoding="latin1", low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    before = len(df)
    df = df.dropna(how="all")
    log.info(f"  dropped {before - len(df):,} fully-blank rows (trailing blank rows in source CSV)")

    df["permalink"] = df["permalink"].str.lower().str.strip()
    df["funding_total_usd"] = clean_currency_string(df["funding_total_usd"])

    df = null_out_impossible_years(df, ["founded_at", "first_funding_at", "last_funding_at"])

    round_cols = [
        "seed", "venture", "equity_crowdfunding", "undisclosed", "convertible_note",
        "debt_financing", "angel", "grant", "private_equity", "post_ipo_equity",
        "post_ipo_debt", "secondary_market", "product_crowdfunding",
        "round_A", "round_B", "round_C", "round_D", "round_E", "round_F", "round_G", "round_H",
    ]
    for c in round_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    log.info(f"  investments_VC cleaned: {len(df):,} rows retained")
    return df


def load_success_fail() -> pd.DataFrame:
    log.info("Loading big_startup_secsees_dataset.csv")
    df = pd.read_csv(RAW_DIR / "big_startup_secsees_dataset.csv", encoding="utf-8", low_memory=False)
    df["permalink"] = df["permalink"].str.lower().str.strip()
    df["funding_total_usd"] = clean_currency_string(df["funding_total_usd"])
    df = null_out_impossible_years(df, ["founded_at", "first_funding_at", "last_funding_at"])

    # Flag (don't drop) pre-1900 founding dates -- legitimate old orgs
    # (universities, the Red Cross, etc.) that analysts may want to exclude
    # from "startup" trend analysis but shouldn't be silently destroyed.
    founded_year = pd.to_datetime(df["founded_at"], errors="coerce").dt.year
    df["is_pre_1900_founding"] = founded_year < MIN_VALID_YEAR
    n_flagged = df["is_pre_1900_founding"].sum()
    log.info(f"  flagged {n_flagged} rows founded before {MIN_VALID_YEAR} (kept, not dropped)")

    log.info(f"  success_fail cleaned: {len(df):,} rows retained")
    return df


def load_unicorns() -> pd.DataFrame:
    log.info("Loading global_unicorn_companies.csv")
    df = pd.read_csv(RAW_DIR / "global_unicorn_companies.csv", encoding="utf-8-sig", low_memory=False)

    # Fix known industry data-entry errors
    for company, correct_industry in UNICORN_INDUSTRY_FIXES.items():
        mask = df["company"] == company
        n = mask.sum()
        if n:
            log.info(f"  fixing industry for '{company}': -> '{correct_industry}'")
            df.loc[mask, "industry"] = correct_industry

    # Standardize country -> ISO3 for joinability with the other two datasets
    df["country_iso3"] = df["country"].map(COUNTRY_NAME_TO_ISO3_OVERRIDES)
    try:
        import pycountry
        unmapped = df["country_iso3"].isna() & df["country"].notna()

        def lookup(name):
            try:
                return pycountry.countries.lookup(name).alpha_3
            except LookupError:
                return None

        df.loc[unmapped, "country_iso3"] = df.loc[unmapped, "country"].map(lookup)
    except ImportError:
        log.info("  pycountry not installed -- relying on manual override table only")

    still_unmapped = df["country_iso3"].isna() & df["country"].notna()
    log.info(f"  country -> ISO3 mapping: {still_unmapped.sum()} of {df['country'].notna().sum()} unmapped")
    if still_unmapped.sum():
        log.info(f"  unmapped countries: {sorted(df.loc[still_unmapped, 'country'].unique())}")

    df["date_joined"] = pd.to_datetime(df["date_joined"], errors="coerce")
    df["company_key"] = df["company"].str.lower().str.strip()

    log.info(f"  unicorns cleaned: {len(df):,} rows retained")
    return df


def build_fact_funding_rounds(vc: pd.DataFrame, sf: pd.DataFrame) -> pd.DataFrame:
    """
    Merges investments_VC (round-level detail) with success_fail (clean
    status labels) on permalink. Strategy:
      - Start from investments_VC as the base (richer financial detail).
      - Bring in the clean `status` label from success_fail (overwrite,
        since success_fail's status field has 0% nulls vs vc's 11.4%).
      - Append the 17,662 companies present ONLY in success_fail (with
        round-level columns left null, since we have no detail for them).
    """
    log.info("Merging investments_VC + success_fail into fact_funding_rounds")

    sf_status = sf[["permalink", "status", "is_pre_1900_founding"]].rename(
        columns={"status": "status_clean"}
    )
    merged = vc.merge(sf_status, on="permalink", how="left")
    merged["status"] = merged["status_clean"].fillna(merged["status"])
    merged = merged.drop(columns=["status_clean"])
    merged["is_pre_1900_founding"] = merged["is_pre_1900_founding"].fillna(False)

    vc_keys = set(vc["permalink"].dropna())
    sf_only = sf[~sf["permalink"].isin(vc_keys)].copy()
    # Align columns: sf_only won't have the round-level breakdown columns
    for col in merged.columns:
        if col not in sf_only.columns:
            sf_only[col] = pd.NA

    fact = pd.concat([merged, sf_only[merged.columns]], ignore_index=True)

    dup_count = fact.duplicated(subset=["permalink"]).sum()
    if dup_count:
        log.info(f"  {dup_count} duplicate permalinks after merge -- keeping first occurrence")
        fact = fact.drop_duplicates(subset=["permalink"], keep="first")

    # Primary category (first entry in the pipe-delimited category_list).
    # NOTE: category_list values often have leading/trailing pipes
    # (e.g. '|Entertainment|Politics|News|'), so a naive split()[0] grabs
    # an empty string -- strip pipes first, then split on the cleaned value.
    def first_category(val):
        if pd.isna(val):
            return pd.NA
        parts = [p for p in str(val).strip("|").split("|") if p]
        return parts[0] if parts else pd.NA

    def category_count(val):
        if pd.isna(val):
            return pd.NA
        return len([p for p in str(val).strip("|").split("|") if p])

    fact["primary_category"] = fact["category_list"].apply(first_category)
    fact["category_count"] = fact["category_list"].apply(category_count)

    log.info(f"  fact_funding_rounds built: {len(fact):,} rows, {fact.shape[1]} columns")
    return fact


def run():
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    vc = load_investments_vc()
    sf = load_success_fail()
    uc = load_unicorns()

    fact = build_fact_funding_rounds(vc, sf)

    # Tag unicorns onto the fact table via company name + country.
    # IMPORTANT: name-only matching fans out on shared names across
    # different companies (e.g. "Bolt" = US fintech vs Estonian mobility
    # unicorn; "Fabric" appears twice in the unicorn list under the same
    # country too) -- this silently duplicated fact rows in an earlier
    # version of this pipeline. Joining on (name, country) and deduping
    # the unicorn side first fixes both issues.
    fact["company_key"] = fact["name"].astype(str).str.lower().str.strip()
    uc_join_key = ["company_key", "country_iso3"]
    uc_dupes = uc.duplicated(subset=uc_join_key).sum()
    if uc_dupes:
        log.info(f"  {uc_dupes} unicorn rows share an identical (name, country) key -- keeping first, dropping rest before join")
    uc_dedup = uc.drop_duplicates(subset=uc_join_key, keep="first")

    uc_slim = uc_dedup[uc_join_key + ["valuation_billion_usd", "date_joined", "valuation_tier", "select_investors"]].rename(
        columns={"date_joined": "unicorn_date_joined", "country_iso3": "country_code"}
    )
    pre_merge_rows = len(fact)
    fact = fact.merge(uc_slim, on=["company_key", "country_code"], how="left")
    assert len(fact) == pre_merge_rows, "Unicorn merge changed row count -- fan-out bug reintroduced"

    fact["is_unicorn"] = fact["valuation_billion_usd"].notna()
    log.info(f"  matched {fact['is_unicorn'].sum():,} companies to the unicorn list by (name, country)")

    fact.to_csv(PROCESSED_DIR / "fact_funding_rounds_clean.csv", index=False,
    encoding="utf-8")
    uc.to_csv(PROCESSED_DIR / "dim_unicorns_clean.csv", index=False,encoding="utf-8")

    log.info(f"Saved cleaned outputs to {PROCESSED_DIR}")
    return fact, uc


if __name__ == "__main__":
    run()
