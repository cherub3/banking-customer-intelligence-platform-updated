"""
self_test.py — Standalone deployment self-test for the warehouse bootstrap.

Run this anywhere the app will run (locally, in CI, or via a Streamlit Cloud
"Manage app" shell) to verify the full chain — imports, paths, bootstrap,
DuckDB creation, and a real query — works before trusting `streamlit run`.

Usage:
    python python/self_test.py

Exits with status 0 if every check passes, 1 otherwise.
"""
import sys
import traceback
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

RESULTS = []


def check(name: str):
    """Decorator that runs a check function, records PASS/FAIL, and never raises."""
    def decorator(fn):
        try:
            fn()
            RESULTS.append((name, True, None))
        except Exception as exc:
            RESULTS.append((name, False, f"{type(exc).__name__}: {exc}"))
        return fn
    return decorator


@check("Import bootstrap module")
def _check_import_bootstrap():
    global bootstrap
    import bootstrap  # noqa: F401


@check("Import generate_data module")
def _check_import_generate_data():
    import generate_data  # noqa: F401


@check("Import run_pipeline module")
def _check_import_run_pipeline():
    import run_pipeline  # noqa: F401


@check("Import duckdb / pandas")
def _check_import_deps():
    import duckdb       # noqa: F401
    import pandas       # noqa: F401


@check("Repository folder structure")
def _check_folder_structure():
    import bootstrap
    required = [bootstrap.ROOT, bootstrap.DATA_DIR, bootstrap.SQL_DIR, bootstrap.PYTHON_DIR]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required directories: {missing}")


@check("Path resolution is absolute and consistent")
def _check_path_resolution():
    import bootstrap
    if not bootstrap.DB_PATH.is_absolute():
        raise AssertionError(f"DB_PATH is not absolute: {bootstrap.DB_PATH}")
    if not str(bootstrap.DB_PATH).endswith("banking_platform.duckdb"):
        raise AssertionError(f"Unexpected DB_PATH: {bootstrap.DB_PATH}")


@check("SQL layer files present")
def _check_sql_files():
    import bootstrap
    layers = [
        "00_schema.sql", "01_customer_360.sql", "02_rfm_scoring.sql",
        "03_segmentation.sql", "04_health_scoring.sql", "05_concentration.sql",
        "06_rm_actions.sql", "07_exceptions.sql", "08_executive_kpis.sql", "09_views.sql",
    ]
    missing = [f for f in layers if not (bootstrap.SQL_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing SQL files: {missing}")


@check("Bootstrap builds (or confirms) the warehouse")
def _check_bootstrap_builds():
    import bootstrap
    bootstrap.build_db_if_missing()
    if not bootstrap.check_db():
        raise RuntimeError("build_db_if_missing() returned but check_db() is False")


@check("DuckDB file created and non-empty")
def _check_db_file():
    import bootstrap
    if not bootstrap.DB_PATH.exists():
        raise FileNotFoundError(str(bootstrap.DB_PATH))
    if bootstrap.DB_PATH.stat().st_size == 0:
        raise AssertionError("Database file is empty")


@check("Read-only connection + query execution")
def _check_query_execution():
    import duckdb
    import bootstrap
    con = duckdb.connect(str(bootstrap.DB_PATH), read_only=True)
    try:
        row = con.execute("SELECT COUNT(*) FROM fct_customer_360").fetchone()
        if row is None or row[0] == 0:
            raise AssertionError("fct_customer_360 returned no rows")
    finally:
        con.close()


def main() -> int:
    print("=" * 64)
    print("Streamlit Banking Platform — Deployment Self-Test")
    print("=" * 64)

    for name, passed, error in RESULTS:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if error:
            print(f"       -> {error}")

    n_pass = sum(1 for _, p, _ in RESULTS if p)
    n_total = len(RESULTS)
    print("-" * 64)
    print(f"{n_pass}/{n_total} checks passed")
    print("=" * 64)

    if n_pass < n_total:
        print("\nFailing check tracebacks:\n")
        for name, passed, error in RESULTS:
            if not passed:
                print(f"--- {name} ---")
                print(error)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
