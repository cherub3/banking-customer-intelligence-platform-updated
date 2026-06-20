"""
Management Pack — pre-formatted monthly business review for leadership.
Designed for screenshots, printing, and PDF export.
Audience: CFO, Portfolio Head, Risk Committee, Board.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.db import get_executive_summary, get_exceptions
from utils.styles import page_header, section_title, kpi_card, C

# ── Data ──────────────────────────────────────────────────────────────────────
kpis   = get_executive_summary()
p1_exc = get_exceptions("P1")

rev_ltm   = kpis.get("portfolio_revenue_ltm", 1_711_764)
rev_qoq   = kpis.get("revenue_qoq_pct", -3.4)
rev_90d   = kpis.get("revenue_current_90d", 406_840)
rev_prior = kpis.get("revenue_prior_90d", 421_020)
rev_risk  = kpis.get("revenue_at_risk", 879_206)
conc_pct  = kpis.get("revenue_concentration_pct", 51.4)
dep_score = kpis.get("revenue_dependency_score", "CRITICAL")
active    = int(kpis.get("active_customers", 860))
total     = int(kpis.get("total_customers", 1000))
dormant   = int(kpis.get("dormant_customers", 140))
healthy_p = kpis.get("healthy_pct", 28.9)
crit_p    = kpis.get("critical_pct", 14.0)
p1_n      = int(kpis.get("open_p1_exceptions", 4))
open_exc  = int(kpis.get("open_exceptions", 652))
retain_n  = int(kpis.get("open_retain_actions", 102))
react_n   = int(kpis.get("open_reactivation_actions", 140))
xsell_n   = int(kpis.get("open_crosssell_actions", 93))

# ── Sidebar hint ──────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.info(
    "**Export this report**\n\n"
    "Right-click the page → Print → "
    "Save as PDF, or take a screenshot for your management pack."
)

# ── Report Header ─────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{C['navy']};color:white;padding:1.75rem 2.25rem;
                border-radius:10px;margin-bottom:1.5rem">
        <div style="font-size:1.35rem;font-weight:800;letter-spacing:0.01em">
            Monthly Business Review
        </div>
        <div style="font-size:0.85rem;opacity:0.8;margin-top:0.25rem">
            Banking Customer Intelligence Platform &nbsp;·&nbsp; Portfolio Snapshot: January 2024
        </div>
        <div style="display:flex;gap:2.5rem;margin-top:1.1rem;font-size:0.8rem;opacity:0.9">
            <span>📅 &nbsp;31 January 2024</span>
            <span>👥 &nbsp;1,000 customers</span>
            <span>💳 &nbsp;152,502 transactions</span>
            <span>📊 &nbsp;9-layer SQL analytics pipeline</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Portfolio At a Glance ─────────────────────────────────────────────────────
section_title("Portfolio At a Glance")

a1, a2, a3 = st.columns(3)
b1, b2, b3 = st.columns(3)

with a1:
    st.markdown(kpi_card(
        "Portfolio Revenue (LTM)",
        f"£{rev_ltm:,.0f}",
        sub="Last 12 months fee income",
    ), unsafe_allow_html=True)

with a2:
    st.markdown(kpi_card(
        "Revenue Change (QoQ)",
        f"{rev_qoq:+.1f}%",
        delta=f"{'▲' if rev_qoq >= 0 else '▼'} £{abs(rev_90d - rev_prior):,.0f} vs prior quarter",
        delta_positive=(rev_qoq >= 0),
        sub=f"£{rev_90d:,.0f} current · £{rev_prior:,.0f} prior",
    ), unsafe_allow_html=True)

with a3:
    st.markdown(kpi_card(
        "Revenue at Risk",
        f"£{rev_risk:,.0f}",
        badge_text=dep_score,
        badge_color="#FFFFFF",
        badge_bg=C["red"],
        sub=f"Exposed if top 10 exit · {conc_pct:.1f}% concentration",
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:0.6rem'></div>", unsafe_allow_html=True)

with b1:
    st.markdown(kpi_card(
        "Active Customers",
        f"{active:,} / {total:,}",
        sub=f"{dormant} dormant (14.0%) · zero revenue contribution",
    ), unsafe_allow_html=True)

with b2:
    st.markdown(kpi_card(
        "Portfolio Health",
        f"{healthy_p:.0f}% Healthy",
        sub=f"53.3% Watchlist · 3.8% At-Risk · {crit_p:.0f}% Critical",
    ), unsafe_allow_html=True)

with b3:
    st.markdown(kpi_card(
        "Open P1 Exceptions",
        str(p1_n),
        badge_text="Immediate Action",
        badge_color="#FFFFFF",
        badge_bg=C["red"],
        sub=f"{open_exc} total exceptions · {retain_n} Retain actions open",
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:0.25rem'></div>", unsafe_allow_html=True)

# ── Key Findings ──────────────────────────────────────────────────────────────
section_title("Key Findings")

findings = [
    (
        "1",
        C["red"],
        "Revenue Concentration: CRITICAL",
        f"The top 10 clients generate <b>£{rev_risk:,.0f} ({conc_pct:.1f}%)</b> of all portfolio fee income. "
        f"The revenue gap between rank #10 (£76,573) and rank #11 (£5,735) is 13×. "
        f"Portfolio revenue dependency is rated <b>CRITICAL</b> — the highest severity level. "
        f"A single VIP exit removes ~£87,921 in annual fee income.",
    ),
    (
        "2",
        C["red"],
        "P1 Alert: Four VIP Clients Showing Revenue Decline",
        f"Evans LLC (−22.7%), Lee Marsden and Evans (−29.0%), Thomas and Sons (−22.5%), and Palmer Group (−24.8%) "
        f"recorded revenue declines of 22–29% in the current quarter. Combined quarterly revenue fell "
        f"from £97,915 to £73,682 (−£24,233). All four clients remain Healthy in overall health score "
        f"— the exception monitor detected this signal ahead of standard category-level reporting.",
    ),
    (
        "3",
        C["orange"],
        "Portfolio Revenue Declined 3.4% Quarter-on-Quarter",
        f"Portfolio fee revenue fell from £{rev_prior:,.0f} to £{rev_90d:,.0f} "
        f"(−{abs(rev_qoq):.1f}%). The decline is concentrated in two segments: {dormant} Dormant accounts "
        f"averaging −95.0% revenue change (effectively zero revenue), and 227 At-Risk customers averaging "
        f"−42.2% revenue change. The Regular segment remains stable and is not a contributor to the decline "
        f"(+7.5% average). If left unaddressed, the At-Risk and Dormant decline will compound.",
    ),
    (
        "4",
        C["amber"],
        "Early Warning: 24 Healthy Customers Showing Deteriorating Trend",
        "24 customers currently classified as Healthy (health score ≥70) are already on a Deteriorating "
        "health trend — invisible to standard exception monitoring. These customers represent a preventive "
        "intervention window. Proactive RM contact now is significantly cheaper than retention action once "
        "they fall to Watchlist or At-Risk status.",
    ),
]

for num, border_c, title, body in findings:
    st.markdown(
        f'<div style="border:1px solid #DEE2E6;border-left:4px solid {border_c};'
        f'border-radius:0 8px 8px 0;padding:1.1rem 1.4rem;margin-bottom:0.75rem;background:white">'
        f'<div style="font-size:0.65rem;font-weight:800;color:{border_c};'
        f'text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.3rem">Finding {num}</div>'
        f'<div style="font-weight:700;color:{C["navy"]};font-size:0.92rem;margin-bottom:0.4rem">'
        f'{title}</div>'
        f'<div style="font-size:0.82rem;color:#495057;line-height:1.55">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Priority Action Agenda ────────────────────────────────────────────────────
section_title("Priority Action Agenda")

agenda = pd.DataFrame([
    {"Priority": "P1", "SLA": "24 hours",  "Action": "Retain",
     "Customers": 4,   "Owner": "Senior RM",
     "Description": "Call 4 VIP clients with revenue decline. Identify cause, agree retention plan."},
    {"Priority": "P2", "SLA": "3 days",    "Action": "Retain",
     "Customers": 101, "Owner": "RM Team",
     "Description": "Contact At-Risk and deteriorating customers before further revenue erosion."},
    {"Priority": "P2", "SLA": "3 days",    "Action": "Exceptions",
     "Customers": 117, "Owner": "RM Ops",
     "Description": "Triage 117 Segment Downgrade exceptions. Assign Retain or Reactivate action."},
    {"Priority": "P3", "SLA": "7 days",    "Action": "Reactivate",
     "Customers": react_n, "Owner": "RM Team",
     "Description": "Contact dormant customers. Tiered outreach by time-since-last-transaction."},
    {"Priority": "P3", "SLA": "7 days",    "Action": "Review",
     "Customers": 157, "Owner": "RM Team",
     "Description": "Assess early-warning accounts. Escalate to Retain if decline confirmed."},
    {"Priority": "P3", "SLA": "7 days",    "Action": "Cross-Sell",
     "Customers": xsell_n, "Owner": "RM Team",
     "Description": "Present product proposals to healthy, growing customers at next touchpoint."},
])

st.dataframe(
    agenda,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Priority":    st.column_config.TextColumn("Priority"),
        "SLA":         st.column_config.TextColumn("SLA"),
        "Action":      st.column_config.TextColumn("Action"),
        "Customers":   st.column_config.NumberColumn("Customers"),
        "Owner":       st.column_config.TextColumn("Owner"),
        "Description": st.column_config.TextColumn("Instructions", width="large"),
    },
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="margin-top:1.5rem;padding:1rem 1.5rem;background:{C["light_bg"]};'
    f'border-radius:8px;border:1px solid {C["border"]}">'
    f'<div style="font-size:0.72rem;color:{C["muted"]};line-height:1.8">'
    f'<b>Generated by:</b> Banking Customer Intelligence & Risk Analytics Platform<br>'
    f'<b>Data period:</b> LTM 1 Feb 2023 – 31 Jan 2024 · Current quarter: 3 Nov 2023 – 31 Jan 2024<br>'
    f'<b>Source:</b> 152,502 transactions · 1,000 customers · 9 analytical SQL layers · DuckDB analytics engine<br>'
    f'<b>Methodology:</b> RFM scoring · 5-segment model · 4-dimension health scoring · '
    f'Revenue concentration analysis · Automated exception detection'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)
