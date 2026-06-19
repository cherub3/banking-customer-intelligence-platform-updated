"""
RM Action Centre — prioritised action workbook for Relationship Managers.
Every customer has one action. Sorted by priority. Filter by RM, segment, or action type.
Audience: Relationship Managers, Team Leaders, RM Operations.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.db import get_rm_actions, get_action_breakdown
from utils.styles import page_header, section_title, kpi_card, C
from utils.charts import action_type_bar, PLOT_CFG

# ── Data ──────────────────────────────────────────────────────────────────────
action_df = get_action_breakdown()

p1_n = int(action_df[action_df["priority"] == "P1"]["n"].sum()) if not action_df.empty else 0
p2_n = int(action_df[action_df["priority"] == "P2"]["n"].sum()) if not action_df.empty else 0
p3_n = int(action_df[action_df["priority"] == "P3"]["n"].sum()) if not action_df.empty else 0
p4_n = int(action_df[action_df["priority"] == "P4"]["n"].sum()) if not action_df.empty else 0

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.markdown(f'<b style="font-size:0.8rem;color:{C["navy"]}">WORKBOOK FILTERS</b>',
                    unsafe_allow_html=True)

priority_filter = st.sidebar.multiselect(
    "Priority",
    ["P1", "P2", "P3", "P4"],
    default=["P1", "P2", "P3"],
    help="P4 = Monitor (no active intervention needed)",
)
type_filter = st.sidebar.multiselect(
    "Action Type",
    ["Retain", "Review", "Cross-Sell", "Reactivate"],
    default=[],
    placeholder="All action types",
)
segment_filter = st.sidebar.multiselect(
    "Segment",
    ["VIP", "Growth", "Regular", "At-Risk", "Dormant"],
    default=[],
    placeholder="All segments",
)

# ── Fetch with filters ────────────────────────────────────────────────────────
workbook = get_rm_actions(
    priorities=priority_filter if len(priority_filter) < 4 else None,
    action_types=type_filter if type_filter else None,
    rms=None,
)
if segment_filter:
    workbook = workbook[workbook["segment"].isin(segment_filter)]

# ── Page header ───────────────────────────────────────────────────────────────
page_header(
    "RM Action Centre",
    f"Showing {len(workbook):,} actions · Sorted by priority · One action per customer",
)

# ── Priority KPI Cards ────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(kpi_card(
        "P1 — Act within 24 hours",
        str(p1_n),
        badge_text="Senior RM",
        badge_color="#FFFFFF",
        badge_bg=C["red"],
        sub="VIP revenue decline — urgent retention",
    ), unsafe_allow_html=True)

with c2:
    st.markdown(kpi_card(
        "P2 — Act within 3 days",
        str(p2_n),
        badge_text="RM Team",
        badge_color="#FFFFFF",
        badge_bg=C["orange"],
        sub="Retain + Cross-sell high-value accounts",
    ), unsafe_allow_html=True)

with c3:
    st.markdown(kpi_card(
        "P3 — Act within 7 days",
        str(p3_n),
        sub="Reactivate + Review + Cross-sell",
    ), unsafe_allow_html=True)

with c4:
    st.markdown(kpi_card(
        "P4 — 30-day review cycle",
        str(p4_n),
        sub="Monitor — no immediate intervention",
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

# ── Action Breakdown Chart ─────────────────────────────────────────────────────
section_title("Action Distribution")

left, right = st.columns([3, 2])

with left:
    if not action_df.empty:
        fig = action_type_bar(action_df, title="Actions by Type and Priority")
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

with right:
    st.markdown(
        f'<div style="padding:1rem;background:{C["sky"]};border-radius:8px;height:100%">'
        f'<div style="font-size:0.75rem;font-weight:800;color:{C["navy"]};'
        f'text-transform:uppercase;letter-spacing:0.07em;margin-bottom:1rem">'
        f'Action Type Definitions</div>'
        + "".join([
            f'<div style="margin-bottom:0.75rem">'
            f'<span style="font-weight:700;color:{C["navy"]}">{name}</span>'
            f'<div style="font-size:0.78rem;color:#495057;margin-top:0.1rem">{desc}</div>'
            f'</div>'
            for name, desc in [
                ("Retain", "Protect a declining relationship. Contact to understand concerns and prevent churn."),
                ("Review", "Early warning — RM to assess and escalate to Retain if needed."),
                ("Cross-Sell", "Healthy, engaged customer. Present product upgrade at next touchpoint."),
                ("Reactivate", "Dormant account. Contact to re-engage and offer product review."),
                ("Monitor", "Stable — no active intervention. Review at standard 30-day cadence."),
            ]
        ])
        + f'</div>',
        unsafe_allow_html=True,
    )

# ── RM Workbook Table ─────────────────────────────────────────────────────────
section_title(f"RM Workbook — {len(workbook):,} Actions")

if workbook.empty:
    st.info("No actions match the selected filters. Adjust the sidebar to view more actions.")
else:
    display_cols = [
        "priority", "sla_days", "customer_name", "segment",
        "health_category", "health_trend", "revenue_ltm",
        "revenue_delta_pct", "action_type", "action_description", "assigned_rm",
    ]
    show_df = workbook[display_cols].copy()

    st.dataframe(
        show_df,
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config={
            "priority":          st.column_config.TextColumn("Priority"),
            "sla_days":          st.column_config.NumberColumn("SLA (days)"),
            "customer_name":     st.column_config.TextColumn("Customer", width="medium"),
            "segment":           st.column_config.TextColumn("Segment"),
            "health_category":   st.column_config.TextColumn("Health"),
            "health_trend":      st.column_config.TextColumn("Trend"),
            "revenue_ltm":       st.column_config.NumberColumn("LTM Revenue", format="£%.0f"),
            "revenue_delta_pct": st.column_config.NumberColumn("QoQ %", format="%.1f%%"),
            "action_type":       st.column_config.TextColumn("Action"),
            "action_description":st.column_config.TextColumn("Instructions", width="large"),
            "assigned_rm":       st.column_config.TextColumn("RM"),
        },
    )

    # Quick breakdown below the table
    type_counts = workbook["action_type"].value_counts()
    summary_parts = [f"<b>{t}</b>: {n}" for t, n in type_counts.items()]
    st.markdown(
        f'<div style="font-size:0.75rem;color:{C["muted"]};margin-top:0.4rem">'
        f'{len(workbook):,} actions shown · '
        + " · ".join(summary_parts)
        + f' · P4 Monitor actions excluded by default'
        + f'</div>',
        unsafe_allow_html=True,
    )
