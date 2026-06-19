"""
Risk & Exceptions — operational alert feed for the RM operations team.
Audience: RM Operations, Portfolio Risk, Senior Relationship Managers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.db import get_exceptions, get_exception_breakdown
from utils.styles import page_header, section_title, kpi_card, exception_card, C
from utils.charts import exception_bar, donut, PLOT_CFG

# ── Data ──────────────────────────────────────────────────────────────────────
all_exc  = get_exceptions()
p1_exc   = get_exceptions("P1")
p2_exc   = get_exceptions("P2")
exc_bkdn = get_exception_breakdown()

p1_n  = int((all_exc["severity"] == "P1").sum()) if not all_exc.empty else 0
p2_n  = int((all_exc["severity"] == "P2").sum()) if not all_exc.empty else 0
p3_n  = int((all_exc["severity"] == "P3").sum()) if not all_exc.empty else 0
total = p1_n + p2_n + p3_n

# ── Page header ───────────────────────────────────────────────────────────────
page_header(
    "Risk & Exceptions",
    f"{total} open exceptions detected · {p1_n} P1 require immediate senior RM action",
)

# ── P1 Alert Banner ───────────────────────────────────────────────────────────
st.markdown(
    f'<div style="background:#FFEBEE;border-left:4px solid {C["red"]};'
    f'border-radius:0 8px 8px 0;padding:0.85rem 1.25rem;margin-bottom:1.25rem">'
    f'<span style="font-weight:800;color:{C["red"]};font-size:0.82rem;'
    f'text-transform:uppercase;letter-spacing:0.06em">'
    f'🔴 &nbsp;{p1_n} P1 Exceptions Active</span>'
    f'<span style="font-size:0.82rem;color:#B71C1C;margin-left:0.75rem">'
    f'Revenue decline of 22–29% detected on VIP clients. '
    f'Senior RM contact required within <b>24 hours</b>. '
    f'Log all contact attempts for escalation.'
    f'</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI Row ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(kpi_card(
        "Total Open Exceptions",
        str(total),
        sub="Across 5 exception types",
    ), unsafe_allow_html=True)

with c2:
    st.markdown(kpi_card(
        "P1 — Immediate (24h)",
        str(p1_n),
        badge_text="VIP Revenue Decline",
        badge_color="#FFFFFF",
        badge_bg=C["red"],
    ), unsafe_allow_html=True)

with c3:
    st.markdown(kpi_card(
        "P2 — Urgent (3 days)",
        str(p2_n),
        sub="Critical customers + downgrades",
    ), unsafe_allow_html=True)

with c4:
    st.markdown(kpi_card(
        "P3 — Routine (7 days)",
        str(p3_n),
        sub="Activity cliffs + revenue decline",
    ), unsafe_allow_html=True)

# ── P1 Exception Detail Cards ─────────────────────────────────────────────────
section_title("P1 Exceptions — Immediate Action Required")

if p1_exc.empty:
    st.success("No P1 exceptions detected.")
else:
    cols = st.columns(min(len(p1_exc), 4))
    for i, (_, row) in enumerate(p1_exc.iterrows()):
        cname  = row.get("customer_name", "")
        rev    = row.get("revenue_ltm", 0) or 0
        r90    = row.get("revenue_90d", 0) or 0
        delta  = row.get("revenue_delta_pct", 0) or 0
        etype  = row.get("exception_type", "")
        rec    = row.get("recommended_action", "")
        with cols[i % len(cols)]:
            st.markdown(
                f'<div style="background:white;border:1px solid #FFCDD2;'
                f'border-top:4px solid {C["red"]};border-radius:4px;padding:1.1rem 1.2rem;height:100%">'
                f'<div style="font-size:0.65rem;font-weight:800;color:{C["red"]};'
                f'text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.4rem">'
                f'P1 · {etype}'
                f'</div>'
                f'<div style="font-size:0.95rem;font-weight:700;color:{C["navy"]}">{cname}</div>'
                f'<div style="font-size:0.8rem;color:#495057;margin-top:0.5rem;line-height:1.5">'
                f'LTM Revenue: <b>£{rev:,.0f}</b><br>'
                f'Current 90d: <b>£{r90:,.0f}</b><br>'
                f'QoQ Change: <b style="color:{C["red"]}">{delta:+.1f}%</b>'
                f'</div>'
                f'<div style="font-size:0.73rem;color:{C["muted"]};margin-top:0.6rem;'
                f'background:{C["light_bg"]};border-radius:4px;padding:0.4rem 0.6rem">'
                f'{rec}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

# ── Exception Breakdown + Severity Split ──────────────────────────────────────
section_title("Exception Breakdown")

left, right = st.columns([3, 2])

with left:
    if not exc_bkdn.empty:
        fig = exception_bar(exc_bkdn, title="Exceptions by Type and Severity")
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

with right:
    sev_counts = all_exc["severity"].value_counts()
    fig = donut(
        labels=["P1 — Immediate", "P2 — Urgent", "P3 — Routine"],
        values=[
            int(sev_counts.get("P1", 0)),
            int(sev_counts.get("P2", 0)),
            int(sev_counts.get("P3", 0)),
        ],
        colors=[C["red"], C["orange"], C["amber"]],
        center_label="exceptions",
        center_value=str(total),
        title="Severity Distribution",
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)

# ── Filters + Full Exception Table ────────────────────────────────────────────
section_title("Exception Feed")

f1, f2 = st.columns(2)
with f1:
    type_filter = st.multiselect(
        "Exception Type",
        options=sorted(all_exc["exception_type"].unique().tolist()),
        default=[],
        placeholder="All types",
    )
with f2:
    sev_filter = st.multiselect(
        "Severity",
        options=["P1", "P2", "P3"],
        default=[],
        placeholder="All severities",
    )

filtered = all_exc.copy()
if type_filter:
    filtered = filtered[filtered["exception_type"].isin(type_filter)]
if sev_filter:
    filtered = filtered[filtered["severity"].isin(sev_filter)]

display_cols = [
    "severity", "exception_type", "customer_name", "segment",
    "health_category", "revenue_ltm", "revenue_delta_pct",
    "description", "recommended_action", "assigned_rm",
]
show_df = filtered[display_cols].copy()

st.dataframe(
    show_df,
    use_container_width=True,
    height=460,
    hide_index=True,
    column_config={
        "severity":          st.column_config.TextColumn("Severity"),
        "exception_type":    st.column_config.TextColumn("Type", width="medium"),
        "customer_name":     st.column_config.TextColumn("Customer", width="medium"),
        "segment":           st.column_config.TextColumn("Segment"),
        "health_category":   st.column_config.TextColumn("Health"),
        "revenue_ltm":       st.column_config.NumberColumn("LTM Revenue", format="£%.0f"),
        "revenue_delta_pct": st.column_config.NumberColumn("QoQ %", format="%.1f%%"),
        "description":       st.column_config.TextColumn("Description", width="large"),
        "recommended_action":st.column_config.TextColumn("Action", width="large"),
        "assigned_rm":       st.column_config.TextColumn("RM"),
    },
)

st.markdown(
    f'<div style="font-size:0.75rem;color:{C["muted"]};margin-top:0.4rem">'
    f'{len(filtered):,} exceptions shown · Sorted by severity then revenue impact · '
    f'Status: OPEN · Detected: 31 January 2024'
    f'</div>',
    unsafe_allow_html=True,
)
