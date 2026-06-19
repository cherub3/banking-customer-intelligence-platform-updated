"""
styles.py — Color system, CSS injection, and HTML component builders.
"""
import streamlit as st

# ── Color System ──────────────────────────────────────────────────────────────

C = {
    "navy":      "#1B3A6B",
    "steel":     "#4A6FA5",
    "sky":       "#E8F0FB",
    "red":       "#C62828",
    "orange":    "#E65100",
    "amber":     "#F57C00",
    "green":     "#2E7D32",
    "purple":    "#4A148C",
    "muted":     "#6C757D",
    "border":    "#DEE2E6",
    "light_bg":  "#F8F9FA",
    "white":     "#FFFFFF",
}

HEALTH_COLORS = {
    "Healthy":   C["green"],
    "Watchlist": C["amber"],
    "At-Risk":   C["orange"],
    "Critical":  C["purple"],
}

HEALTH_BG = {
    "Healthy":   "#E8F5E9",
    "Watchlist": "#FFFDE7",
    "At-Risk":   "#FFF3E0",
    "Critical":  "#F3E5F5",
}

SEGMENT_COLORS = {
    "VIP":     C["navy"],
    "Growth":  C["green"],
    "Regular": C["steel"],
    "At-Risk": C["orange"],
    "Dormant": C["muted"],
}

PRIORITY_COLORS = {
    "P1": C["red"],
    "P2": C["orange"],
    "P3": C["amber"],
    "P4": C["green"],
}

TREND_COLORS = {
    "Improving":    C["green"],
    "Stable":       C["steel"],
    "Deteriorating": C["red"],
}

# ── CSS ───────────────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
div[data-testid="stToolbar"]     { display: none; }
div[data-testid="stDecoration"]  { display: none; }
div[data-testid="stStatusWidget"]{ display: none; }

.main .block-container {
    padding-top: 1.25rem;
    padding-bottom: 2rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    max-width: 1400px;
}

/* Sidebar brand */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* KPI cards */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #DEE2E6;
    border-radius: 8px;
    padding: 1.1rem 1.25rem 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    height: 100%;
    min-height: 108px;
}
.kpi-label {
    font-size: 0.65rem;
    color: #6C757D;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.4rem;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: #1B3A6B;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}
.kpi-delta-neg { color: #C62828; font-size: 0.78rem; margin-top: 0.25rem; }
.kpi-delta-pos { color: #2E7D32; font-size: 0.78rem; margin-top: 0.25rem; }
.kpi-sub { color: #6C757D; font-size: 0.78rem; margin-top: 0.2rem; }
.kpi-badge {
    display: inline-block;
    border-radius: 3px;
    padding: 1px 8px;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    margin-top: 0.35rem;
}

/* Section title */
.section-title {
    font-size: 0.75rem;
    font-weight: 800;
    color: #1B3A6B;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    padding-bottom: 0.35rem;
    border-bottom: 2px solid #1B3A6B;
    margin-bottom: 0.9rem;
    margin-top: 1.4rem;
}

/* Page header */
.page-header {
    border-bottom: 1px solid #DEE2E6;
    padding-bottom: 0.9rem;
    margin-bottom: 1.25rem;
}
.page-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #1B3A6B;
    display: inline;
}
.page-badge {
    display: inline-block;
    margin-left: 0.75rem;
    font-size: 0.7rem;
    background: #E8F0FB;
    color: #1B3A6B;
    border-radius: 4px;
    padding: 3px 10px;
    font-weight: 700;
    vertical-align: middle;
}
.page-subtitle {
    font-size: 0.85rem;
    color: #6C757D;
    margin-top: 0.2rem;
}

/* Alert banners */
.alert-p1 {
    background: #FFEBEE;
    border-left: 4px solid #C62828;
    border-radius: 0 6px 6px 0;
    padding: 0.9rem 1.25rem;
    margin-bottom: 0.6rem;
}
.alert-p2 {
    background: #FFF3E0;
    border-left: 4px solid #E65100;
    border-radius: 0 6px 6px 0;
    padding: 0.9rem 1.25rem;
    margin-bottom: 0.6rem;
}
.alert-info {
    background: #E8F0FB;
    border-left: 4px solid #1B3A6B;
    border-radius: 0 6px 6px 0;
    padding: 0.9rem 1.25rem;
    margin-bottom: 0.6rem;
}

/* Exception card */
.exc-card {
    background: white;
    border: 1px solid #FFCDD2;
    border-left: 4px solid #C62828;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin-bottom: 0.6rem;
}
.exc-title { font-weight: 700; color: #C62828; font-size: 0.85rem; }
.exc-body  { color: #495057; font-size: 0.82rem; margin-top: 0.3rem; line-height: 1.4; }

/* Insight box */
.insight-box {
    background: white;
    border: 1px solid #DEE2E6;
    border-top: 3px solid #1B3A6B;
    border-radius: 0 0 8px 8px;
    padding: 1.1rem 1.25rem;
    height: 100%;
}
.insight-title { font-weight: 700; color: #1B3A6B; font-size: 0.85rem; margin-bottom: 0.4rem; }
.insight-body  { color: #495057; font-size: 0.82rem; line-height: 1.5; }

/* Management pack report */
.report-header {
    background: #1B3A6B;
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
}
.report-title { font-size: 1.3rem; font-weight: 800; }
.report-sub   { font-size: 0.85rem; opacity: 0.8; margin-top: 0.2rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── HTML Component Builders ───────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="page-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="page-header">
        <span class="page-title">{title}</span>
        <span class="page-badge">JANUARY 2024</span>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str,
             delta: str = "", delta_positive: bool = None,
             sub: str = "",
             badge_text: str = "", badge_color: str = "#1B3A6B",
             badge_bg: str = "#E8F0FB") -> str:
    delta_html = ""
    if delta:
        cls = "kpi-delta-pos" if delta_positive else "kpi-delta-neg"
        delta_html = f'<div class="{cls}">{delta}</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    badge_html = ""
    if badge_text:
        badge_html = (
            f'<div class="kpi-badge" '
            f'style="background:{badge_bg};color:{badge_color}">'
            f'{badge_text}</div>'
        )
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}{sub_html}{badge_html}'
        f'</div>'
    )


def alert_p1(text: str) -> None:
    st.markdown(f'<div class="alert-p1">{text}</div>', unsafe_allow_html=True)


def insight_box(title: str, body: str) -> str:
    return (
        f'<div class="insight-box">'
        f'<div class="insight-title">{title}</div>'
        f'<div class="insight-body">{body}</div>'
        f'</div>'
    )


def exception_card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="exc-card">'
        f'<div class="exc-title">{title}</div>'
        f'<div class="exc-body">{body}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def health_badge(category: str) -> str:
    color = HEALTH_COLORS.get(category, C["muted"])
    bg    = HEALTH_BG.get(category, C["light_bg"])
    return f'<span style="background:{bg};color:{color};border-radius:3px;padding:1px 7px;font-size:0.7rem;font-weight:700">{category}</span>'


def sidebar_portfolio_card(kpis: dict) -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        **Portfolio** · Jan 2024
        {kpis.get('total_customers', 1000):,} customers
        £{kpis.get('portfolio_revenue_ltm', 0):,.0f} LTM
        Concentration: **{kpis.get('revenue_dependency_score', 'CRITICAL')}**
        P1 Alerts: **{kpis.get('open_p1_exceptions', 4)}**
        """
    )
