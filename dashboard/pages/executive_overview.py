"""
Executive Overview — portfolio-level KPIs, concentration risk, and P1 alerts.
Audience: CFO, Head of Relationship Banking, Portfolio Risk Committee.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.db import (
    get_executive_summary, get_top_customers,
    get_health_distribution, get_trend_distribution, get_exceptions,
)
from utils.styles import page_header, section_title, kpi_card, insight_box, C
from utils.charts import (
    concentration_donut, health_donut, trend_donut,
    top_customers_bar, PLOT_CFG,
)

# ── Data ──────────────────────────────────────────────────────────────────────
kpis     = get_executive_summary()
top10    = get_top_customers(10)
health_d = get_health_distribution()
trend_d  = get_trend_distribution()
p1_exc   = get_exceptions("P1")

rev_ltm    = kpis.get("portfolio_revenue_ltm", 1_711_764)
rev_qoq    = kpis.get("revenue_qoq_pct", -3.4)
active     = int(kpis.get("active_customers", 860))
total      = int(kpis.get("total_customers", 1000))
dormant_r  = kpis.get("dormant_rate_pct", 14.0)
conc_pct   = kpis.get("revenue_concentration_pct", 51.4)
dep_score  = kpis.get("revenue_dependency_score", "CRITICAL")
p1_count   = int(kpis.get("open_p1_exceptions", 4))
rev_risk   = kpis.get("revenue_at_risk", 879_206)
rev_90d    = kpis.get("revenue_current_90d", 406_840)
healthy_p  = kpis.get("healthy_pct", 28.9)
open_exc   = int(kpis.get("open_exceptions", 652))

# ── Page header ───────────────────────────────────────────────────────────────
page_header(
    "Executive Overview",
    "1,000 customers · 152,502 transactions · 9-layer analytics pipeline",
)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    delta_dir = rev_qoq >= 0
    delta_sym = "▲" if delta_dir else "▼"
    st.markdown(kpi_card(
        "Portfolio Revenue (LTM)",
        f"£{rev_ltm:,.0f}",
        delta=f"{delta_sym} {abs(rev_qoq):.1f}% vs prior quarter",
        delta_positive=delta_dir,
        sub=f"£{rev_90d:,.0f} current 90 days",
    ), unsafe_allow_html=True)

with c2:
    st.markdown(kpi_card(
        "Active Customers",
        f"{active:,} / {total:,}",
        sub=f"{dormant_r:.1f}% dormant ({total - active} accounts)",
    ), unsafe_allow_html=True)

with c3:
    badge_bg = C["red"] if dep_score == "CRITICAL" else C["orange"]
    st.markdown(kpi_card(
        "Concentration Risk",
        f"{conc_pct:.1f}%",
        sub="Top 10 clients · top 20 = 54.5%",
        badge_text=dep_score,
        badge_color="#FFFFFF",
        badge_bg=badge_bg,
    ), unsafe_allow_html=True)

with c4:
    st.markdown(kpi_card(
        "P1 Alerts Open",
        str(p1_count),
        sub="VIP revenue decline 22–29%",
        badge_text="Immediate Action",
        badge_color="#FFFFFF",
        badge_bg=C["red"],
    ), unsafe_allow_html=True)

with c5:
    st.markdown(kpi_card(
        "Revenue at Risk",
        f"£{rev_risk:,.0f}",
        sub=f"{conc_pct:.1f}% of portfolio exposed",
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

# ── Concentration · Health · Trend ────────────────────────────────────────────
section_title("Portfolio Intelligence")

ca, cb, cc = st.columns(3)

with ca:
    fig = concentration_donut(conc_pct, rev_ltm, title="Revenue Concentration")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

with cb:
    fig = health_donut(health_d, title="Health Distribution")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

with cc:
    fig = trend_donut(trend_d, title="Health Trend")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

# ── Top 10 bar + P1 alert cards ───────────────────────────────────────────────
section_title("Revenue Leaders & Active Alerts")

left, right = st.columns([6, 4])

with left:
    st.markdown(
        f'<div style="font-size:0.82rem;color:{C["muted"]};margin-bottom:0.4rem">'
        f'All top 10 clients are <b style="color:{C["green"]}">Healthy</b> · '
        f'Revenue cliff: rank #10 = £76,573 → rank #11 = £5,735 (13×)'
        f'</div>',
        unsafe_allow_html=True,
    )
    fig = top_customers_bar(top10, title="")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

with right:
    st.markdown(
        f'<div style="background:#FFEBEE;border-left:4px solid {C["red"]};'
        f'border-radius:0 8px 8px 0;padding:0.7rem 1.1rem;margin-bottom:0.9rem">'
        f'<span style="font-size:0.72rem;font-weight:800;color:{C["red"]};'
        f'text-transform:uppercase;letter-spacing:0.07em">'
        f'🔴 &nbsp;{p1_count} P1 Alerts — Senior RM Action Within 24 Hours'
        f'</span></div>',
        unsafe_allow_html=True,
    )
    for _, row in p1_exc.iterrows():
        cname = row.get("customer_name", "")
        delta = row.get("revenue_delta_pct", 0) or 0
        rev   = row.get("revenue_ltm", 0) or 0
        r90   = row.get("revenue_90d", 0) or 0
        etype = row.get("exception_type", "")
        st.markdown(
            f'<div style="background:white;border:1px solid #FFCDD2;'
            f'border-left:4px solid {C["red"]};border-radius:0 8px 8px 0;'
            f'padding:0.8rem 1rem;margin-bottom:0.55rem">'
            f'<div style="font-weight:700;color:{C["navy"]};font-size:0.88rem">'
            f'{cname}</div>'
            f'<div style="font-size:0.78rem;color:#495057;margin-top:0.25rem">'
            f'LTM Revenue: <b>£{rev:,.0f}</b> &nbsp;·&nbsp; '
            f'Current 90d: <b>£{r90:,.0f}</b> &nbsp;·&nbsp; '
            f'Change: <b style="color:{C["red"]}">{delta:+.1f}%</b>'
            f'</div>'
            f'<div style="font-size:0.7rem;color:{C["red"]};margin-top:0.2rem;font-weight:600">'
            f'VIP · {etype}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="font-size:0.75rem;color:{C["muted"]};margin-top:0.5rem;'
        f'background:{C["light_bg"]};border-radius:6px;padding:0.6rem 0.9rem">'
        f'<b>{open_exc}</b> total exceptions open · '
        f'<b>{healthy_p:.0f}%</b> of portfolio is Healthy'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Insight strip ─────────────────────────────────────────────────────────────
section_title("Key Insights")
ia, ib, ic = st.columns(3)

with ia:
    st.markdown(insight_box(
        "Revenue Dependency: CRITICAL",
        "10 clients generate <b>51.4% of all portfolio revenue</b>. The revenue cliff between "
        "rank #10 (£76,573) and rank #11 (£5,735) is 13×. A single VIP exit removes ~£87,921 "
        "in annual fee income — equivalent to 51 Regular-tier customers combined.",
    ), unsafe_allow_html=True)

with ib:
    st.markdown(insight_box(
        "Early Warning: 24 Healthy Customers Deteriorating",
        "<b>24 customers currently classified as Healthy</b> are already on a Deteriorating trend "
        "— invisible to category-based monitoring. Without preventive RM contact, these accounts "
        "will appear in Watchlist exceptions next quarter.",
    ), unsafe_allow_html=True)

with ic:
    st.markdown(insight_box(
        "Reactivation Pipeline: 140 Dormant Accounts",
        "<b>140 customers (14%)</b> have made zero transactions in 90+ days. "
        "Their combined LTM revenue contribution is under £2,000. "
        "The reactivation window is closing — recently dormant accounts have significantly "
        "higher recovery rates than long-term inactive ones.",
    ), unsafe_allow_html=True)
