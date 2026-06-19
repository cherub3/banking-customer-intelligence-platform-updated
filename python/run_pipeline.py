"""
run_pipeline.py
Orchestrates the full analytics pipeline:
  1. Create schema
  2. Load reference and raw data
  3. Execute SQL analytical layers in order
Run from the project root: python python/run_pipeline.py
"""

import logging
import sys
from pathlib import Path

import duckdb
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "banking_platform.duckdb"
SQL_DIR = ROOT / "sql"
RAW_DIR = ROOT / "data" / "raw"
REF_DIR = ROOT / "data" / "reference"

# Order matters — each layer depends on the previous
SQL_LAYERS = [
    "01_customer_360.sql",
    "02_rfm_scoring.sql",
    "03_segmentation.sql",
    "04_health_scoring.sql",
    "05_concentration.sql",
    "06_rm_actions.sql",
    "07_exceptions.sql",
    "08_executive_kpis.sql",
    "09_views.sql",
]

# CSV → table mapping (load order: references before facts)
LOAD_ORDER = [
    ("dim_relationship_managers", REF_DIR / "relationship_managers.csv"),
    ("dim_products",              REF_DIR / "product_catalogue.csv"),
    ("dim_customers",             RAW_DIR / "customers.csv"),
    ("stg_transactions",          RAW_DIR / "transactions.csv"),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def check_data_files() -> None:
    missing = [path for _, path in LOAD_ORDER if not path.exists()]
    if missing:
        log.error("Missing data files. Run  python python/generate_data.py  first.")
        for f in missing:
            log.error(f"  Not found: {f}")
        sys.exit(1)


def execute_sql_file(con: duckdb.DuckDBPyConnection, filepath: Path) -> None:
    """
    Execute a SQL file statement by statement.
    Strips -- comment lines before splitting on semicolons so that semicolons
    inside comments (e.g. 'first; second') do not break the parser.
    The original SQL file is unchanged — comments are only removed in memory.
    """
    raw = filepath.read_text(encoding="utf-8")
    # Remove single-line comment lines before splitting
    stripped_lines = [
        line for line in raw.splitlines()
        if not line.strip().startswith("--")
    ]
    sql = "\n".join(stripped_lines)
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        con.execute(stmt)


# ── Pipeline stages ────────────────────────────────────────────────────────────

def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    log.info("Creating schema …")
    execute_sql_file(con, SQL_DIR / "00_schema.sql")
    log.info("  Schema ready.")


def load_data(con: duckdb.DuckDBPyConnection) -> None:
    log.info("Loading data …")
    for table, filepath in LOAD_ORDER:
        df = pd.read_csv(filepath)

        # Ensure date columns are strings (DuckDB handles ISO strings fine)
        for col in df.columns:
            if "date" in col.lower():
                df[col] = df[col].astype(str)

        con.execute(f"DELETE FROM {table}")
        con.register("_staging", df)
        con.execute(f"INSERT INTO {table} SELECT * FROM _staging")
        con.unregister("_staging")
        log.info(f"  {table:<30}: {len(df):>8,} rows")


def run_sql_layers(con: duckdb.DuckDBPyConnection) -> None:
    log.info("Running analytical layers …")
    for filename in SQL_LAYERS:
        path = SQL_DIR / filename
        if not path.exists():
            log.warning(f"  SKIP  {filename}  (file not found — build it in Phase 2)")
            continue
        log.info(f"  Running  {filename} …")
        execute_sql_file(con, path)
        log.info(f"  ✓  {filename}")


def print_summary(con: duckdb.DuckDBPyConnection) -> None:
    log.info("")
    log.info("── Pipeline Summary ──────────────────────────────────────────")

    checks = [
        ("stg_transactions",   "Transactions loaded"),
        ("dim_customers",      "Customers loaded"),
        ("fct_customer_360",   "Customer 360 records"),
        ("fct_customer_health","Health-scored customers"),
        ("fct_rm_actions",     "RM actions generated"),
        ("fct_exceptions",     "Exceptions detected"),
        ("fct_executive_kpis", "Executive KPI snapshots"),
    ]

    for table, label in checks:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            log.info(f"  {label:<32}: {count:>8,}")
        except Exception:
            log.info(f"  {label:<32}: (not yet built)")

    # Quick concentration check if available
    try:
        row = con.execute("""
            SELECT top_10_pct, revenue_dependency_score
            FROM fct_concentration
            LIMIT 1
        """).fetchone()
        if row:
            log.info("")
            log.info(f"  Revenue concentration (top 10): {row[0]:.1f}%  [{row[1]}]")
    except Exception:
        pass

    log.info("─────────────────────────────────────────────────────────────")
    log.info(f"  Database: {DB_PATH}")
    log.info("")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    check_data_files()

    log.info(f"Connecting to database: {DB_PATH}")
    con = duckdb.connect(str(DB_PATH))

    try:
        create_schema(con)
        load_data(con)
        run_sql_layers(con)
        print_summary(con)
    finally:
        con.close()

    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
