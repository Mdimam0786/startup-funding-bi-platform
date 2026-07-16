"""
Theme system: design tokens + CSS injection for dark/light mode.

Design direction: near-black navy / clean off-white surfaces, an
indigo -> violet -> pink gradient as the single recurring accent,
Inter for UI text, JetBrains Mono for KPI figures and tabular data.
Inspired by Linear / Stripe Dashboard / Databricks workspace chrome --
rounded cards, restrained motion, one bold gradient moment (KPI cards),
everything else disciplined.
"""

DARK = {
    "bg": "#0A0E17",
    "bg_secondary": "#0D1119",
    "surface": "#12161F",
    "surface_hover": "#1A1F2B",
    "border": "#232838",
    "text_primary": "#E6E9F0",
    "text_secondary": "#8B92A8",
    "text_muted": "#5B6178",
    "accent_1": "#6366F1",   # indigo
    "accent_2": "#8B5CF6",   # violet
    "accent_3": "#EC4899",   # pink
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#3B82F6",
    "shadow": "rgba(0, 0, 0, 0.45)",
}

LIGHT = {
    "bg": "#F7F8FA",
    "bg_secondary": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface_hover": "#F1F3F7",
    "border": "#E5E7EB",
    "text_primary": "#0F1420",
    "text_secondary": "#5B6178",
    "text_muted": "#8B92A8",
    "accent_1": "#6366F1",
    "accent_2": "#8B5CF6",
    "accent_3": "#EC4899",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "info": "#2563EB",
    "shadow": "rgba(15, 20, 32, 0.08)",
}


def get_tokens(mode: str) -> dict:
    return DARK if mode == "dark" else LIGHT


def build_css(mode: str) -> str:
    t = get_tokens(mode)
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {{
    --bg: {t['bg']};
    --bg-secondary: {t['bg_secondary']};
    --surface: {t['surface']};
    --surface-hover: {t['surface_hover']};
    --border: {t['border']};
    --text-primary: {t['text_primary']};
    --text-secondary: {t['text_secondary']};
    --text-muted: {t['text_muted']};
    --accent-1: {t['accent_1']};
    --accent-2: {t['accent_2']};
    --accent-3: {t['accent_3']};
    --success: {t['success']};
    --warning: {t['warning']};
    --danger: {t['danger']};
    --info: {t['info']};
    --shadow: {t['shadow']};
    --gradient-main: linear-gradient(135deg, {t['accent_1']} 0%, {t['accent_2']} 55%, {t['accent_3']} 100%);
    --radius-lg: 16px;
    --radius-md: 12px;
    --radius-sm: 8px;
}}

html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.stApp {{
    background: var(--bg);
    color: var(--text-primary);
    transition: background-color 0.25s ease, color 0.25s ease;
}}

/* Hide default Streamlit chrome for a cleaner product feel */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header[data-testid="stHeader"] {{background: transparent;}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] > div {{
    padding-top: 1.2rem;
}}

/* Main content fade-in */
.main .block-container {{
    animation: fadeInUp 0.45s ease both;
    padding-top: 1.5rem;
    max-width: 1300px;
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
/* ---------------- Typography ---------------- */

.stApp,
.stMarkdown,
.stCaption {{
    color: var(--text-primary);
}}

h1,
h2,
h3,
h4,
h5,
h6 {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
}}

p,
label {{
    color: var(--text-primary);
}}

.subtle {{
    color: var(--text-secondary) !important;
    font-weight: 400;
}}

.mono{{
    font-family: 'JetBrains Mono', monospace;
}}

/* ---------------- Card primitives ---------------- */
.app-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem 1.5rem;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}}
.app-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 28px var(--shadow);
    border-color: var(--accent-1);
}}

/* ---------------- Gradient KPI card ---------------- */
.kpi-card {{
    border-radius: var(--radius-lg);
    padding: 1.3rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s cubic-bezier(.2,.8,.2,1), box-shadow 0.2s ease;
    box-shadow: 0 6px 20px var(--shadow);
}}

.kpi-card,
.kpi-card * {{
    color: #FFFFFF !important;
}}
 
.kpi-card:hover {{
    transform: translateY(-5px) scale(1.01);
    box-shadow: 0 16px 34px var(--shadow);
}}
.kpi-card::after {{
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 85% 0%, rgba(255,255,255,0.16), transparent 55%);
}}
.kpi-label {{
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    opacity: 0.88;
    position: relative;
    z-index: 1;
}}
.kpi-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 700;
    margin-top: 0.35rem;
    position: relative;
    z-index: 1;
    line-height: 1.15;
}}
.kpi-delta {{
    font-size: 0.78rem;
    margin-top: 0.4rem;
    opacity: 0.92;
    position: relative;
    z-index: 1;
    font-weight: 500;
}}
.kpi-grad-1 {{ background: linear-gradient(135deg, #6366F1, #4F46E5); }}
.kpi-grad-2 {{ background: linear-gradient(135deg, #8B5CF6, #7C3AED); }}
.kpi-grad-3 {{ background: linear-gradient(135deg, #EC4899, #DB2777); }}
.kpi-grad-4 {{ background: linear-gradient(135deg, #10B981, #059669); }}
.kpi-grad-5 {{ background: linear-gradient(135deg, #3B82F6, #2563EB); }}
.kpi-grad-6 {{ background: linear-gradient(135deg, #F59E0B, #D97706); }}

/* ---------------- Status badge / pill ---------------- */
.pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--surface-hover);
    border: 1px solid var(--border);
    color: var(--text-secondary);
}}
.pill-dot {{
    width: 6px; height: 6px; border-radius: 50%;
}}
.pill-live .pill-dot {{ background: var(--success); box-shadow: 0 0 6px var(--success); }}
.pill-static .pill-dot {{ background: var(--text-muted); }}
.pill-warn .pill-dot {{ background: var(--warning); }}

/* ---------------- Nav item ---------------- */
.nav-section-label {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin: 1.1rem 0 0.4rem 0.2rem;
}}

/* ---------------- Skeleton loader ---------------- */
.skeleton {{
    background: linear-gradient(90deg, var(--surface) 25%, var(--surface-hover) 50%, var(--surface) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
    border-radius: var(--radius-md);
    height: 90px;
}}
@keyframes shimmer {{
    0% {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ---------------- Hero ---------------- */
.hero-title {{
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    background: var(--gradient-main);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero-sub {{
    font-size: 1.05rem;
    color: var(--text-secondary);
    margin-top: 0.6rem;
    max-width: 640px;
}}

/* Buttons */
.stButton > button {{
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-primary);
    font-weight: 600;
    transition: all .2s ease;
}}
.stButton > button:disabled {{
    color: var(--text-muted);
    border-color: var(--border);
    opacity: 0.7;
}}

.stButton > button:hover {{
    background: var(--surface-hover);
    border-color: var(--accent-1);
    color: var(--accent-1);
}}

.stButton > button:focus {{
    box-shadow: none;
}}
a {{
    color: var(--accent-1);
    text-decoration: none;
    transition: color .2s ease;
}}

a:hover {{
    color: var(--accent-2);
}}
input,
textarea,
select {{
    color: var(--text-primary);
}}
[data-baseweb="select"] *,
[data-baseweb="input"] *,
[data-testid="stMetric"] *,
[data-testid="stMarkdownContainer"] * {{
    color: inherit;
}}
.js-plotly-plot {{
    border-radius: var(--radius-md);
}}
hr {{
    border: none;
    border-top: 1px solid var(--border);
}}

</style>
"""