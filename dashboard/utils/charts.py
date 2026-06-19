"""
charts.py — Plotly chart builders. All charts use the same visual language.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from .styles import C, HEALTH_COLORS, SEGMENT_COLORS, TREND_COLORS, PRIORITY_COLORS

PLOT_CFG = dict(displayModeBar=False, responsive=True)

_FONT = dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
             size=12, color="#333333")

def _base(margin=None, height=None, **kw) -> dict:
    m = margin or dict(l=8, r=8, t=36, b=8)
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=_FONT,
        margin=m,
    )
    if height:
        d["height"] = height
    d.update(kw)
    return d


# ── Donut chart ───────────────────────────────────────────────────────────────

def donut(labels: list, values: list, colors: list,
          center_label: str = "", center_value: str = "",
          title: str = "", height: int = 265) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker_colors=colors,
        textinfo="percent",
        textfont=dict(size=11),
        hovertemplate="%{label}<br><b>%{value:,}</b> customers (%{percent})<extra></extra>",
    ))
    if center_value:
        fig.add_annotation(
            text=f"<b>{center_value}</b><br><span style='font-size:10px'>{center_label}</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=C["navy"]),
            align="center",
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=C["navy"]), x=0, pad=dict(l=0)),
        showlegend=True,
        legend=dict(orientation="v", x=1.01, y=0.5, font=dict(size=10)),
        **_base(margin=dict(l=0, r=110, t=32, b=0), height=height),
    )
    return fig


def health_donut(health_df: pd.DataFrame, title="Health Distribution") -> go.Figure:
    return donut(
        labels=health_df["health_category"].tolist(),
        values=health_df["n"].tolist(),
        colors=[HEALTH_COLORS.get(h, C["muted"]) for h in health_df["health_category"]],
        center_label="customers",
        center_value=f"{health_df['n'].sum():,}",
        title=title,
    )


def trend_donut(trend_df: pd.DataFrame, title="Health Trend") -> go.Figure:
    return donut(
        labels=trend_df["health_trend"].tolist(),
        values=trend_df["n"].tolist(),
        colors=[TREND_COLORS.get(t, C["muted"]) for t in trend_df["health_trend"]],
        title=title,
    )


def concentration_donut(top10_pct: float, total_revenue: float, title="Revenue Concentration") -> go.Figure:
    remainder_pct = 100 - top10_pct
    return donut(
        labels=["Top 10 Clients", "Remaining 990"],
        values=[top10_pct, remainder_pct],
        colors=[C["navy"], C["border"]],
        center_label="Top 10",
        center_value=f"{top10_pct:.1f}%",
        title=title,
    )


# ── Horizontal bar — top customers ───────────────────────────────────────────

def top_customers_bar(df: pd.DataFrame, title="Top Customers by Revenue") -> go.Figure:
    df = df.sort_values("revenue_ltm")  # ascending so highest is at top
    health_col = [HEALTH_COLORS.get(h, C["steel"]) for h in df["health_category"]]

    fig = go.Figure(go.Bar(
        x=df["revenue_ltm"],
        y=df["customer_name"].str[:28],        # truncate long names
        orientation="h",
        marker_color=health_col,
        marker_line_width=0,
        text=[f"£{v:,.0f}" for v in df["revenue_ltm"]],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>LTM Revenue: £%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=C["navy"]), x=0),
        xaxis=dict(
            showgrid=True, gridcolor="#F0F0F0",
            tickformat=",.0f", tickprefix="£",
            showticklabels=True,
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        **_base(margin=dict(l=8, r=70, t=36, b=8), height=340),
    )
    return fig


# ── Exception breakdown bar ────────────────────────────────────────────────────

def exception_bar(df: pd.DataFrame, title="Exception Breakdown") -> go.Figure:
    sev_order  = ["P1", "P2", "P3"]
    sev_colors = {s: PRIORITY_COLORS[s] for s in sev_order}

    fig = go.Figure()
    for sev in sev_order:
        sub = df[df["severity"] == sev]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            name=sev,
            x=sub["n"],
            y=sub["exception_type"],
            orientation="h",
            marker_color=sev_colors[sev],
            text=sub["n"],
            textposition="outside",
            textfont=dict(size=10),
            hovertemplate=f"<b>%{{y}}</b><br>{sev}: %{{x}} exceptions<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=C["navy"]), x=0),
        barmode="group",
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        legend=dict(title="Severity", orientation="h", x=0, y=-0.15, font=dict(size=11)),
        **_base(margin=dict(l=8, r=50, t=36, b=40), height=320),
    )
    return fig


# ── Action type bar ────────────────────────────────────────────────────────────

def action_type_bar(df: pd.DataFrame, title="RM Actions by Type & Priority") -> go.Figure:
    action_totals = df.groupby("action_type")["n"].sum().sort_values(ascending=True)
    action_order  = action_totals.index.tolist()
    pri_colors = {p: PRIORITY_COLORS.get(p, C["muted"]) for p in ["P1", "P2", "P3", "P4"]}

    fig = go.Figure()
    for pri in ["P1", "P2", "P3", "P4"]:
        sub = df[df["priority"] == pri]
        if sub.empty:
            continue
        # Align to action_order
        counts = [sub[sub["action_type"] == a]["n"].sum() if a in sub["action_type"].values else 0
                  for a in action_order]
        fig.add_trace(go.Bar(
            name=pri,
            y=action_order,
            x=counts,
            orientation="h",
            marker_color=pri_colors[pri],
            hovertemplate=f"<b>%{{y}}</b> · {pri}: %{{x}} customers<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=C["navy"]), x=0),
        barmode="stack",
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        legend=dict(title="Priority", orientation="h", x=0, y=-0.18, font=dict(size=11)),
        **_base(margin=dict(l=8, r=8, t=36, b=50), height=300),
    )
    return fig


# ── Health heatmap ─────────────────────────────────────────────────────────────

def health_heatmap(pivot: pd.DataFrame, title="Portfolio Health Matrix") -> go.Figure:
    z_vals = pivot.values.tolist()
    text   = [[str(v) if v > 0 else "" for v in row] for row in z_vals]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#EEF2F9"], [0.4, "#7FA7D5"], [1, C["navy"]]],
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=13, color="white"),
        showscale=True,
        colorbar=dict(thickness=12, len=0.8, title=dict(text="Count", side="right")),
        hovertemplate="<b>%{y}</b> — <b>%{x}</b><br>%{z} customers<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=C["navy"]), x=0),
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
        **_base(margin=dict(l=8, r=60, t=60, b=8), height=290),
    )
    return fig


# ── Segment distribution bar ───────────────────────────────────────────────────

def segment_bar(df: pd.DataFrame, title="Customers by Segment") -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df["segment"],
        y=df["n"],
        marker_color=[SEGMENT_COLORS.get(s, C["muted"]) for s in df["segment"]],
        text=df["n"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:,} customers<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=C["navy"]), x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        **_base(height=250),
    )
    return fig


# ── Revenue scatter ────────────────────────────────────────────────────────────

def revenue_health_scatter(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="health_score",
        y="revenue_ltm",
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        hover_name="customer_name",
        hover_data={"health_trend": True, "health_score": True, "revenue_ltm": ":.0f"},
        labels={"health_score": "Health Score", "revenue_ltm": "LTM Revenue (£)"},
        title="Revenue vs Health Score",
    )
    fig.update_traces(marker=dict(size=7, opacity=0.75))
    fig.update_layout(
        yaxis=dict(tickprefix="£", tickformat=",.0f"),
        legend=dict(title="Segment", orientation="v", font=dict(size=11)),
        **_base(height=380),
    )
    return fig
