"""
db.py — Database connection and query helpers.
All queries are cached for 1 hour. Dashboard is read-only.
"""
import duckdb
import pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "banking_platform.duckdb"


@st.cache_data(ttl=3600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(sql).df()
    con.close()
    return df


def get_executive_summary() -> dict:
    df = run_query("SELECT * FROM v_executive_summary")
    return df.iloc[0].to_dict() if not df.empty else {}


def get_concentration() -> dict:
    df = run_query("SELECT * FROM fct_concentration")
    return df.iloc[0].to_dict() if not df.empty else {}


def get_top_customers(n: int = 20) -> pd.DataFrame:
    return run_query(f"SELECT * FROM v_concentration_ladder LIMIT {n}")


def get_health_distribution() -> pd.DataFrame:
    return run_query("""
        SELECT health_category, COUNT(*) AS n
        FROM fct_customer_health
        GROUP BY health_category
        ORDER BY CASE health_category
            WHEN 'Healthy'   THEN 1
            WHEN 'Watchlist' THEN 2
            WHEN 'At-Risk'   THEN 3
            ELSE 4 END
    """)


def get_trend_distribution() -> pd.DataFrame:
    return run_query("""
        SELECT health_trend, COUNT(*) AS n
        FROM fct_customer_health
        GROUP BY health_trend
        ORDER BY CASE health_trend
            WHEN 'Improving'     THEN 1
            WHEN 'Stable'        THEN 2
            ELSE 3 END
    """)


def get_segment_distribution() -> pd.DataFrame:
    return run_query("""
        SELECT segment, COUNT(*) AS n
        FROM fct_customer_segments
        GROUP BY segment
        ORDER BY CASE segment
            WHEN 'VIP'     THEN 1
            WHEN 'Growth'  THEN 2
            WHEN 'Regular' THEN 3
            WHEN 'At-Risk' THEN 4
            ELSE 5 END
    """)


def get_health_heatmap_pivot() -> pd.DataFrame:
    df = run_query("""
        SELECT segment, health_category, SUM(customer_count) AS n
        FROM v_health_heatmap
        GROUP BY segment, health_category
    """)
    row_order = ["VIP", "Growth", "Regular", "At-Risk", "Dormant"]
    col_order = ["Healthy", "Watchlist", "At-Risk", "Critical"]
    pivot = (
        df.pivot_table(index="segment", columns="health_category", values="n", fill_value=0)
          .reindex(index=row_order, columns=col_order, fill_value=0)
    )
    return pivot


def get_all_customers(segments=None, health_cats=None, health_trends=None) -> pd.DataFrame:
    conditions = []
    if segments:
        joined = "', '".join(segments)
        conditions.append(f"s.segment IN ('{joined}')")
    if health_cats:
        joined = "', '".join(health_cats)
        conditions.append(f"h.health_category IN ('{joined}')")
    if health_trends:
        joined = "', '".join(health_trends)
        conditions.append(f"h.health_trend IN ('{joined}')")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return run_query(f"""
        SELECT
            c.customer_name,
            a.customer_id,
            s.segment,
            h.health_category,
            h.health_trend,
            ROUND(h.health_score, 0)        AS health_score,
            ROUND(t.revenue_ltm, 0)         AS revenue_ltm,
            ROUND(t.revenue_90d, 0)         AS revenue_90d,
            ROUND(t.revenue_delta_pct, 1)   AS revenue_qoq_pct,
            t.txn_count_90d,
            t.products_active,
            a.action_type,
            a.priority,
            a.assigned_rm,
            c.region,
            s.segment_change
        FROM fct_rm_actions     a
        JOIN dim_customers      c ON a.customer_id = c.customer_id
        JOIN fct_customer_segments s ON a.customer_id = s.customer_id
        JOIN fct_customer_health   h ON a.customer_id = h.customer_id
        JOIN fct_customer_360      t ON a.customer_id = t.customer_id
        {where}
        ORDER BY t.revenue_ltm DESC
    """)


def get_exceptions(severity: str = None) -> pd.DataFrame:
    where = f"WHERE severity = '{severity}'" if severity else ""
    return run_query(f"SELECT * FROM v_exception_feed {where} ORDER BY severity, revenue_ltm DESC")


def get_exception_breakdown() -> pd.DataFrame:
    return run_query("""
        SELECT exception_type, severity, COUNT(*) AS n
        FROM fct_exceptions
        WHERE status = 'OPEN'
        GROUP BY exception_type, severity
        ORDER BY severity, exception_type
    """)


def get_rm_actions(priorities=None, action_types=None, rms=None) -> pd.DataFrame:
    conditions = ["action_type != 'Monitor'"]
    if priorities:
        joined = "', '".join(priorities)
        conditions.append(f"priority IN ('{joined}')")
    if action_types:
        joined = "', '".join(action_types)
        conditions.append(f"action_type IN ('{joined}')")
    if rms:
        joined = "', '".join(rms)
        conditions.append(f"assigned_rm IN ('{joined}')")
    where = "WHERE " + " AND ".join(conditions)
    return run_query(f"SELECT * FROM v_customer_watchlist {where} ORDER BY priority, revenue_ltm DESC")


def get_action_breakdown() -> pd.DataFrame:
    return run_query("""
        SELECT action_type, priority, COUNT(*) AS n
        FROM fct_rm_actions
        WHERE status = 'OPEN'
        GROUP BY action_type, priority
        ORDER BY action_type, priority
    """)
