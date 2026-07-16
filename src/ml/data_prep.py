"""
Shared feature preparation for all the ML tasks.
Builds a single modeling table from the warehouse, with consistent
encoding so regression, classification, and clustering all start from
the same feature definitions.
"""
from pathlib import Path

import numpy as np
import pandas as pd

WH = str(Path(__file__).resolve().parents[2] / "data" / "warehouse") + "/"


def load_modeling_table():
    fact = pd.read_csv(WH + "fact_startup_funding.csv", low_memory=False)
    startup = pd.read_csv(WH + "dim_startup_with_source_key.csv", low_memory=False)
    geo = pd.read_csv(WH + "dim_geography.csv", low_memory=False)
    industry = pd.read_csv(WH + "dim_industry.csv", low_memory=False)

    df = fact.merge(startup, on="startup_id").merge(geo, on="geography_id", how="left").merge(industry, on="industry_id", how="left")

    # Cap industry/country cardinality: keep top-N, bucket the rest as "Other"
    # -- 812 raw categories and 136 countries would blow up one-hot encoding
    # and mostly just add noise from tiny categories.
    top_industries = df['primary_category'].value_counts().head(15).index
    df['industry_grouped'] = np.where(df['primary_category'].isin(top_industries), df['primary_category'], 'Other')

    top_countries = df['country_name'].value_counts().head(15).index
    df['country_grouped'] = np.where(df['country_name'].isin(top_countries), df['country_name'], 'Other')

    df['is_multi_round'] = df['is_multi_round'].astype(int)
    df['has_debt_financing'] = df['has_debt_financing'].astype(int)

    return df


FEATURE_COLS_NUMERIC = [
    'funding_rounds', 'years_since_founded', 'is_multi_round',
    'num_round_types_used', 'has_debt_financing', 'category_count',
]
FEATURE_COLS_CATEGORICAL = ['industry_grouped', 'country_grouped']
