"""
Customer Intelligence — filter, analyse, and drill into 1,000 customer relationships.
Audience: Portfolio Managers, Relationship Managers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.db import get_all_customers, get_health_heatmap_pivot
from utils.styles import page_header, section_title, kpi_card, C
from utils.charts import health_heatmap, revenue_health_scatter, segment_bar, PLOT_CFG

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.markdown(f'<b style="font-size:0.8rem;color:{C["navy"]}">FILTERS</b>',
                    unsafe_allow_html=True)

segments = st.sidebar.multiselect(
    "Segment",
    ["VIP", "Growth", "Regular", "At-Risk", "Dormant"],
    default=["VIP", "Growth", "Regular", "At-Risk", "Dormant"],
)
health_cats = st.sidebar.multiselect(
    "Health Category",
    ["Healthy", "Watchlist", "At-Risk", "Critical"],
    default=["Healthy", "Watchlist", "At-Risk", "Critical"],
)
health_trends = st.sidebar.multiselect(
    "Health Trend",
    ["Improving", "Stable", "Deteriorating"],
    default=["Improving", "Stable", "Deteriorating"],
)
action_filter = st.sidebar.multiselect(
    "Action Type",
    ["Retain", "Review", "Cross-Sell", "Reactivate", "Monitor"],
    default=["Retain", "Review", "Cross-Sell", "Reactivate", "Monitor"],
)

# ── Data ──────────────────────────────────────────────────────────────────────
df_all = get_all_customers(
    segments if len(segments) < 5 else None,
    health_cats if len(health_cats) < 4 else None,
    health_trends if len(health_trends) < 3 else None,
)
if action_filter and len(action_filter) < 5:
    df_all = df_all[df_all["action_type"].isin(action_filter)]

pivot = get_health_heatmap_pivot()

# ── Page header ───────────────────────────────────────────────────────────────
page_header(
    "Customer Intelligence",
    f"Showing {len(df_all):,} of 1,000 customers — filtered by segment, health, and trend",
)

# ── Dynamic KPI row ───────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

avg_health  = df_all["health_score"].mean() if not df_all.empty else 0
total_rev   = df_all["revenue_ltm"].sum() if not df_all.empty else 0
det_pct     = (df_all["health_trend"] == "Deteriorating").mean() * 100 if not df_all.empty else 0
retain_n    = (df_all["action_type"] == "Retain").sum()

with c1:
    st.markdown(kpi_card(
        "Customers (Filtered)",
        f"{len(df_all):,}",
        sub=f"{len(df_all)/10:.1f}% of portfolio",
    ), unsafe_allow_html=True)

with c2:
    rating_color = C["green"] if avg_health >= 70 else (C["amber"] if avg_health >= 45 else C["red"])
    st.markdown(kpi_card(
        "Avg Health Score",
        f"{avg_health:.0f} / 100",
        sub="Healthy ≥70 · Watchlist 45–69 · At-Risk 25–44 · Critical <25",
    ), unsafe_allow_html=True)

with c3:
    st.markdown(kpi_card(
        "LTM Revenue (Filtered)",
        f"£{total_rev:,.0f}",
        sub=f"{total_rev/1_711_764*100:.1f}% of £1.71M portfolio total",
    ), unsafe_allow_html=True)

with c4:
    delta_pos = det_pct < 20
    st.markdown(kpi_card(
        "Deteriorating Trend",
        f"{det_pct:.1f}%",
        delta=f"{'▼' if delta_pos else '▲'} {abs(det_pct - 24.2):.1f}pp vs portfolio avg",
        delta_positive=delta_pos,
        sub=f"{retain_n} customers require Retain action",
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

# ── Portfolio Health Matrix + Scatter ─────────────────────────────────────────
section_title("Portfolio Health Matrix")

left, right = st.columns([1, 1])

with left:
    fig = health_heatmap(pivot, title="Segment × Health Category (full portfolio)")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    st.markdown(
        f'<div style="font-size:0.75rem;color:{C["muted"]};margin-top:-0.5rem">'
        f'Darker = more customers. Dormant row is all Critical (health score = 0).'
        f'</div>',
        unsafe_allow_html=True,
    )

with right:
    if not df_all.empty:
        fig = revenue_health_scatter(df_all)
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("No customers match the selected filters.")

# ── Customer table ─────────────────────────────────────────────────────────────
section_title("Customer Detail")

if df_all.empty:
    st.warning("No customers match the selected filters. Adjust the sidebar to view data.")
else:
    # Column display order
    display_cols = [
        "customer_name", "segment", "health_category", "health_trend",
        "health_score", "revenue_ltm", "revenue_qoq_pct",
        "txn_count_90d", "products_active", "action_type", "priority", "assigned_rm",
    ]
    show_df = df_all[display_cols].copy()

    st.dataframe(
        show_df,
        use_container_width=True,
        height=440,
        hide_index=True,
        column_config={
            "customer_name":   st.column_config.TextColumn("Customer", width="medium"),
            "segment":         st.column_config.TextColumn("Segment"),
            "health_category": st.column_config.TextColumn("Health"),
            "health_trend":    st.column_config.TextColumn("Trend"),
            "health_score":    st.column_config.ProgressColumn(
                                   "Score", min_value=0, max_value=100, format="%d"),
            "revenue_ltm":     st.column_config.NumberColumn("LTM Revenue", format="£%.0f"),
            "revenue_qoq_pct": st.column_config.NumberColumn("QoQ %", format="%.1f%%"),
            "txn_count_90d":   st.column_config.NumberColumn("Txns (90d)"),
            "products_active": st.column_config.NumberColumn("Products"),
            "action_type":     st.column_config.TextColumn("Action"),
            "priority":        st.column_config.TextColumn("Priority"),
            "assigned_rm":     st.column_config.TextColumn("RM"),
        },
    )

    st.markdown(
        f'<div style="font-size:0.75rem;color:{C["muted"]};margin-top:0.4rem">'
        f'{len(df_all):,} customers shown · Click a column header to sort · '
        f'Health Score: Healthy ≥70 · Watchlist 45–69 · At-Risk 25–44 · Critical &lt;25'
        f'</div>',
        unsafe_allow_html=True,
    )
