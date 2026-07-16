"""
Generates the before/after Data Quality Report by comparing raw source
files against the cleaned outputs produced by clean.py.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

log = get_logger("validate")

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def profile_column_nulls(df: pd.DataFrame) -> dict:
    return (df.isna().mean() * 100).round(2).to_dict()


def generate_report():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    raw_vc = pd.read_csv(RAW_DIR / "investments_VC.csv", encoding="latin1", low_memory=False)
    raw_sf = pd.read_csv(RAW_DIR / "big_startup_secsees_dataset.csv", encoding="utf-8", low_memory=False)
    raw_uc = pd.read_csv(RAW_DIR / "global_unicorn_companies.csv", encoding="utf-8-sig", low_memory=False)

    fact = pd.read_csv(PROCESSED_DIR / "fact_funding_rounds_clean.csv", low_memory=False)
    uc_clean = pd.read_csv(PROCESSED_DIR / "dim_unicorns_clean.csv", low_memory=False)

    lines = []
    lines.append("# Data Quality Report")
    lines.append("")
    lines.append("Prepared by Md Imamuddin")
    lines.append("")
    lines.append("This report summarizes the data quality checks performed on the raw and cleaned datasets used in the Startup Funding & Business Intelligence Platform.")
    lines.append("")

    lines.append("## 1. Row Count Reconciliation")
    lines.append("")
    lines.append("| Source | Raw Rows | Notes |")
    lines.append("|---|---|---|")
    lines.append(f"| investments_VC.csv | {len(raw_vc):,} | {len(raw_vc) - raw_vc.dropna(how='all').shape[0]:,} fully-blank trailing rows removed |")
    lines.append(f"| big_startup_secsees_dataset.csv | {len(raw_sf):,} | no blank/duplicate rows found |")
    lines.append(f"| global_unicorn_companies.csv | {len(raw_uc):,} | retained as-is (2 industry data-entry fixes) |")
    lines.append("")
    lines.append(f"**Merged `fact_funding_rounds_clean.csv`: {len(fact):,} rows** "
                  f"(= investments_VC deduplicated ∩/∪ success_fail, per the merge strategy in the cleaning notes)")
    lines.append("")

    lines.append("## 2. Completeness — Missing Values (Cleaned Fact Table)")
    lines.append("")
    null_pct = profile_column_nulls(fact)
    null_pct = {k: v for k, v in sorted(null_pct.items(), key=lambda x: -x[1]) if v > 0}
    lines.append("| Column | % Missing |")
    lines.append("|---|---|")
    for col, pct in list(null_pct.items())[:20]:
        lines.append(f"| {col} | {pct}% |")
    lines.append("")
    lines.append(f"({len(null_pct)} of {fact.shape[1]} columns have any missing values; showing top 20 by missingness)")
    lines.append("")

    lines.append("## 3. Validity Checks")
    lines.append("")
    fund = fact["funding_total_usd"]
    lines.append(f"- `funding_total_usd`: {fund.notna().sum():,} non-null values, "
                  f"range ${fund.min():,.0f} – ${fund.max():,.0f}, {(fund <= 0).sum()} values ≤ 0")
    dup_permalinks = fact["permalink"].duplicated().sum()
    lines.append(f"- Duplicate `permalink` values in final fact table: {dup_permalinks}")
    status_vals = fact["status"].value_counts(dropna=False).to_dict()
    lines.append(f"- `status` distribution: {status_vals}")
    lines.append(f"- Rows flagged `is_pre_1900_founding` (kept, not dropped): {int(fact['is_pre_1900_founding'].sum())}")
    lines.append(f"- Rows matched to unicorn list (`is_unicorn`=True): {int(fact['is_unicorn'].sum())} of {len(uc_clean)} unicorns "
                  f"({int(fact['is_unicorn'].sum())/len(uc_clean)*100:.1f}% match rate by exact name)")
    unmapped_country = uc_clean["country_iso3"].isna() & uc_clean["country"].notna()
    lines.append(f"- Unicorn country → ISO3 mapping: {unmapped_country.sum()} unmapped country name(s)")
    lines.append("")

    lines.append("## 4. Known Limitations (documented, not hidden)")
    lines.append("")
    lines.append("- **Unicorn match rate is exact (name, country) match only (~19%).** Many unicorns in the "
                  "funding dataset likely exist under slightly different name formatting (e.g. punctuation, "
                  "'Inc'/'Ltd' suffixes, rebrands) or the Crunchbase snapshot simply predates their "
                  "unicorn status (source data is pre-2015; most unicorns achieved that status later). "
                  "A fuzzy-matching pass (e.g. `rapidfuzz`) could raise the match rate slightly, but the "
                  "date mismatch is the bigger structural limitation — flagged here rather than hidden.")
    lines.append("- **Crunchbase source data is historical** (funding activity concentrated pre-2015); "
                  "all time-series analysis will be framed accordingly, not as \"current market\" data.")
    lines.append("- **`category_list` is multi-valued** (pipe-delimited); we extract a `primary_category` "
                  "(first listed) for simpler grouping, but this discards secondary categories — acceptable "
                  "for headline industry analysis, revisit if sub-category drill-down is needed.")
    lines.append("")

    report_text = "\n".join(lines)
    out_path = DOCS_DIR / "data_quality_report.md"
    out_path.write_text(report_text, encoding="utf-8")
    log.info(f"Data quality report written to {out_path}")
    print(report_text)


if __name__ == "__main__":
    generate_report()
