import warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import joblib
import shap

ROOT = Path(__file__).resolve().parents[2]
WH = str(ROOT / "data" / "warehouse") + "/"
OUT = str(ROOT / "docs" / "ml_charts") + "/"

# ---------------- Regression SHAP ----------------
print("Computing SHAP values for regression model...")
reg_model = joblib.load(WH + "regression_model.pkl")
X_test = pd.read_csv(WH + "regression_X_test.csv")

X_test_sample = X_test.sample(n=min(2000, len(X_test)), random_state=42)
X_transformed = reg_model.named_steps['prep'].transform(X_test_sample)
feature_names = (reg_model.named_steps['prep'].named_transformers_['cat']
                  .get_feature_names_out(['industry_grouped', 'country_grouped']).tolist()
                  + ['funding_rounds', 'years_since_founded', 'is_multi_round',
                     'num_round_types_used', 'has_debt_financing', 'category_count'])

explainer = shap.TreeExplainer(reg_model.named_steps['model'])
shap_values = explainer(X_transformed)
shap_values.feature_names = feature_names

fig = plt.figure(figsize=(9, 7))
shap.summary_plot(shap_values, X_transformed, feature_names=feature_names, show=False, max_display=12)
plt.title("SHAP Summary — Funding Amount Regression (log target)")
plt.tight_layout(); plt.savefig(OUT + "01_shap_regression_summary.png", bbox_inches='tight'); plt.close()
print("  saved regression SHAP summary")

# ---------------- Classification SHAP ----------------
print("Computing SHAP values for classification model...")
clf_model = joblib.load(WH + "classification_model.pkl")
X_test_c = pd.read_csv(WH + "classification_X_test.csv")
X_test_c_sample = X_test_c.sample(n=min(2000, len(X_test_c)), random_state=42)
X_transformed_c = clf_model.named_steps['prep'].transform(X_test_c_sample)
if hasattr(X_transformed_c, "toarray"):
    X_transformed_c = X_transformed_c.toarray()
X_transformed_c = np.asarray(X_transformed_c, dtype=float)
feature_names_c = (clf_model.named_steps['prep'].named_transformers_['cat']
                    .get_feature_names_out(['industry_grouped', 'country_grouped']).tolist()
                    + ['funding_rounds', 'years_since_founded', 'is_multi_round',
                       'num_round_types_used', 'has_debt_financing', 'category_count'])

explainer_c = shap.TreeExplainer(clf_model.named_steps['model'])
shap_values_c = explainer_c(X_transformed_c)
# For RandomForestClassifier, shap_values_c has shape (n, features, n_classes); take class 1
if len(shap_values_c.shape) == 3:
    sv_class1 = shap_values_c[:, :, 1]
else:
    sv_class1 = shap_values_c
sv_class1.feature_names = feature_names_c

fig = plt.figure(figsize=(9, 7))
shap.summary_plot(sv_class1, X_transformed_c, feature_names=feature_names_c, show=False, max_display=12)
plt.title("SHAP Summary — Success (Exit) Classification, class=exited")
plt.tight_layout(); plt.savefig(OUT + "02_shap_classification_summary.png", bbox_inches='tight'); plt.close()
print("  saved classification SHAP summary")

print("DONE")
