"""
Use Case 3: Startup Clustering
Unsupervised segmentation of startups into peer groups based on their
funding profile, using K-Means with elbow + silhouette analysis to
choose k, then a business-readable profile of each resulting cluster.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

WH = str(Path(__file__).resolve().parents[2] / "data" / "warehouse") + "/"

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from data_prep import load_modeling_table

df = load_modeling_table()

cluster_features = ['funding_total_usd', 'funding_rounds', 'years_since_founded',
                     'num_round_types_used', 'category_count']
model_df = df.dropna(subset=cluster_features).copy()
print(f"Clustering dataset: {len(model_df):,} rows")

# Log-transform funding (heavily skewed, would otherwise dominate distance calc)
model_df['log_funding'] = np.log1p(model_df['funding_total_usd'])
X_cols = ['log_funding', 'funding_rounds', 'years_since_founded', 'num_round_types_used', 'category_count']
X = model_df[X_cols]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("\n"+"="*80); print("CHOOSING K: ELBOW + SILHOUETTE"); print("="*80)
inertias = []
silhouettes = []
k_range = range(2, 9)
# Use a sample for silhouette (expensive on 60K+ rows)
sample_idx = np.random.RandomState(42).choice(len(X_scaled), size=min(8000, len(X_scaled)), replace=False)

for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    sil = silhouette_score(X_scaled[sample_idx], labels[sample_idx])
    silhouettes.append(sil)
    print(f"k={k}: inertia={km.inertia_:,.0f}, silhouette={sil:.3f}")

best_k = k_range[np.argmax(silhouettes)]
print(f"\nBest k by silhouette score: {best_k}")

print("\n"+"="*80); print(f"FINAL MODEL: K-Means with k={best_k}"); print("="*80)
final_km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
model_df['cluster'] = final_km.fit_predict(X_scaled)

profile = model_df.groupby('cluster').agg(
    count=('startup_id', 'count'),
    median_funding=('funding_total_usd', 'median'),
    avg_funding_rounds=('funding_rounds', 'mean'),
    avg_years_since_founded=('years_since_founded', 'mean'),
    avg_round_types_used=('num_round_types_used', 'mean'),
    exit_rate=('is_exited', 'mean'),
    unicorn_rate=('is_unicorn', 'mean'),
    top_industry=('primary_category', lambda x: x.mode().iloc[0] if not x.mode().empty else None),
).round(2)
profile['pct_of_dataset'] = (profile['count'] / len(model_df) * 100).round(1)
print(profile.to_string())

model_df[['startup_id', 'cluster'] + X_cols].to_csv(
    WH + 'startup_clusters.csv', index=False)
profile.to_csv(WH + 'cluster_profiles.csv')
print("\nSaved cluster assignments and profiles.")
