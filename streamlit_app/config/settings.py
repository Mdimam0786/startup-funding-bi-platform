"""
App-wide settings, paths, and constants.
Single source of truth so nothing hardcodes a path or magic number
in more than one place.
"""
from pathlib import Path

# ---------------- Paths ----------------
APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"
MODELS_DIR = APP_ROOT / "models"
ASSETS_DIR = APP_ROOT / "assets"
CSS_DIR = ASSETS_DIR / "css"

# ---------------- App Metadata ----------------
APP_NAME = "Startup Funding Intelligence"
APP_TAGLINE = "67,098 startups. $833.4B tracked. One platform."
APP_VERSION = "1.0.0"

GITHUB_URL = "https://github.com/Mdimam0786/startup-funding-bi-platform"
LINKEDIN_URL = "https://www.linkedin.com/in/md-imamuddin-5457391a9/"
RESUME_PATH = ASSETS_DIR / "resume.pdf"

# ---------------- Data Files ----------------
FILES = {
    "startup": DATA_DIR / "dim_startup.csv",
    "geography": DATA_DIR / "dim_geography.csv",
    "industry": DATA_DIR / "dim_industry.csv",
    "date": DATA_DIR / "dim_date.csv",
    "round_type": DATA_DIR / "dim_round_type.csv",
    "investor": DATA_DIR / "dim_investor.csv",
    "fact_funding": DATA_DIR / "fact_startup_funding.csv",
    "fact_by_type": DATA_DIR / "fact_funding_by_type.csv",
    "investor_bridge": DATA_DIR / "bridge_investor_unicorn.csv",
    "cluster_profiles": DATA_DIR / "cluster_profiles_k5.csv",
    "startup_clusters": DATA_DIR / "startup_clusters_k5.csv",
    "regression_importance": DATA_DIR / "regression_feature_importance.csv",
    "classification_importance": DATA_DIR / "classification_feature_importance.csv",
}

MODEL_FILES = {
    "regression": MODELS_DIR / "regression_model.pkl",
    "classification": MODELS_DIR / "classification_model.pkl",
}

# ---------------- Headline Numbers (fallback constants) ----------------
# Used for instant-render skeleton states before data finishes loading;
# real values always come from the actual data once cached load completes.
HEADLINE_STATS = {
    "total_startups": 67098,
    "total_funding": 833_442_476_092,
    "total_unicorns": 254,
    "exit_rate": 0.1059,
    "median_funding": 1_750_000,
    "countries": 136,
}

# Historical data scope disclosure -- shown consistently across pages
DATA_SCOPE_NOTE = (
    "Historical Crunchbase snapshot (1995–2015). Trend and growth language "
    "describes that window, not live market conditions."
)
