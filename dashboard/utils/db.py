"""
db.py — Database connection and query helpers.
All queries are cached for 1 hour. Dashboard is read-only.

The warehouse (data/banking_platform.duckdb) is built automatically on first
run if it doesn't exist yet — see python/bootstrap.py. This keeps the .duckdb
file out of git while still letting `streamlit run dashboard/app.py` work on
a fresh clone, locally or on Streamlit Cloud.

IMPORTANT: the check -> build -> verify -> connect sequence below deliberately
does NOT run inside any @st.cache_data / @st.cache_resource function.
Streamlit's caching layer does not reliably propagate st.error()/st.stop()
calls made from inside a cached function — if the build silently fails there,
execution can fall through to a duckdb.connect(read_only=True) against a file
that was never created. That mismatch (works locally where the build always
succeeded; fails identically on every Cloud rerun) was the root cause of the
original deployment failure. Keeping this logic uncached costs one cheap
os.stat() call per rerun and guarantees failures are always visible.
"""
import logging
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

log = logging.getLogger(__name__)

# python/bootstrap.py is the single source of truth for all warehouse paths.
_ROOT = Path(__file__).resolve().parent.parent.parent
_PYTHON_DIR = str(_ROOT / "python")
if _PYTHON_DIR not in sys.path:
    sys.path.insert(0, _PYTHON_DIR)

from bootstrap import (  # noqa: E402  (path insert above must run first)
    BootstrapError,
    DB_PATH,
    build_db_if_missing,
    check_db,
    get_diagnostics,
)

_WAREHOUSE_READY = False  # process-local idempotency flag; build_db_if_missing() is also self-checking


def _fail_safe(title: str, step: str, exc: Exception, remediation: str) -> None:
    """Render a clean, specific error — never a raw duckdb/Python traceback — then halt."""
    st.error(
        f"### ⚠️ {title}\n\n"
        f"**Failed step:** `{step}`\n\n"
        f"**Exception:** `{type(exc).__name__}: {exc}`\n\n"
        f"**What to do:** {remediation}"
    )
    with st.expander("Diagnostics"):
        st.json(get_diagnostics())
    st.stop()


def ensure_warehouse() -> None:
    """
    Enforce: 1) check exists -> 2) build if missing -> 3) verify exists -> 4) caller connects.
    Plain function, NOT cache-decorated — see module docstring for why.
    """
    global _WAREHOUSE_READY
    if _WAREHOUSE_READY:
        return

    log.info(f"Project root: {_ROOT}")
    log.info(f"Database path: {DB_PATH}")
    log.info(f"Database exists: {check_db()}")

    if not check_db():
        log.info("Bootstrap started.")
        try:
            build_db_if_missing()
        except BootstrapError as exc:
            log.exception("Warehouse build failed at step '%s'", exc.step)
            _fail_safe(
                "Warehouse build failed",
                exc.step,
                exc.original,
                "This is almost always a missing dependency, a permissions issue on the "
                "deploy target, or bad source data. Check the app logs for the full "
                "traceback of the failing step, fix the underlying cause, then redeploy "
                "or restart the app — the build will retry automatically since the "
                "database file does not exist yet.",
            )
        except Exception as exc:
            log.exception("Unexpected error while preparing the data warehouse")
            _fail_safe(
                "Warehouse build failed",
                "unknown",
                exc,
                "An unexpected error occurred outside the normal build steps. Check the "
                "app logs for the full traceback, then restart the app.",
            )
        log.info("Bootstrap completed.")

    # Verify — never trust a "no exception" signal alone; this is what
    # prevents falling through to a read-only connect on a missing file.
    if not check_db():
        _fail_safe(
            "Warehouse build failed",
            "verify_db",
            FileNotFoundError(f"{DB_PATH} still does not exist after build."),
            "The build reported success but no database file was produced. This points "
            "to a filesystem issue on the deploy target (e.g. a non-writable data "
            "directory). Check that the app's working directory is writable, then "
            "restart the app.",
        )

    _WAREHOUSE_READY = True


@st.cache_data(ttl=3600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    ensure_warehouse()
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        df = con.execute(sql).df()
        con.close()
        return df
    except duckdb.Error as exc:
        log.exception("DuckDB connection/query failed")
        _fail_safe(
            "Warehouse build failed",
            "connect_readonly",
            exc,
            "The warehouse file exists but DuckDB could not open it read-only — this "
            "usually means the file is corrupt or locked by another process. Delete "
            f"`{DB_PATH}` and restart the app to force a clean rebuild.",
        )


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
