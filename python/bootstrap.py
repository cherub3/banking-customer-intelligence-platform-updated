"""
bootstrap.py — Ensures the DuckDB warehouse exists before the dashboard reads it.

The warehouse file (data/banking_platform.duckdb) is intentionally NOT committed
to the repository (see .gitignore). On first run — locally, on a fresh clone, or
on Streamlit Cloud — this module builds it automatically:

  1. Generate synthetic source CSVs if data/raw is missing them.
  2. Execute the full SQL analytics pipeline.
  3. Leave a ready DuckDB file behind for all subsequent runs.

This module is the SINGLE SOURCE OF TRUTH for all warehouse paths (ROOT,
DATA_DIR, DB_PATH, RAW_DIR). Every other module — dashboard/utils/db.py,
python/self_test.py — imports these constants from here instead of
recomputing them, so there is no way for two parts of the app to disagree
about where the database lives.

build_db_if_missing() is cheap to call on every script rerun: when the file
already exists it does nothing but a single os.stat() call, so it does NOT
need (and must NOT use) Streamlit caching around it. Wrapping warehouse
construction in @st.cache_resource is an anti-pattern here: Streamlit does
not guarantee that st.error()/st.stop() calls inside a cached function
propagate correctly, which is the actual root cause of the Cloud-only
"duckdb.IOException at read_only connect" failure this module fixes — the
build's own failure was being swallowed, so the dashboard fell through to
connecting to a database file that was never created.
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Canonical paths (single source of truth for the whole app) ────────────────
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH  = DATA_DIR / "banking_platform.duckdb"
RAW_DIR  = DATA_DIR / "raw"
REF_DIR  = DATA_DIR / "reference"
SQL_DIR  = ROOT / "sql"
PYTHON_DIR = Path(__file__).resolve().parent

REQUIRED_RAW_FILES = [
    RAW_DIR / "customers.csv",
    RAW_DIR / "transactions.csv",
]


class BootstrapError(RuntimeError):
    """Raised when warehouse construction fails, carrying the failing step name."""

    def __init__(self, step: str, original: Exception):
        self.step = step
        self.original = original
        super().__init__(f"Bootstrap failed at step '{step}': {original}")


def _ensure_python_on_path() -> None:
    p = str(PYTHON_DIR)
    if p not in sys.path:
        sys.path.insert(0, p)


def get_diagnostics() -> dict:
    """Snapshot of path/state info for logging and the sidebar debug panel."""
    return {
        "Project root":        str(ROOT),
        "Database path":       str(DB_PATH),
        "Database exists":     check_db(),
        "Raw data dir":        str(RAW_DIR),
        "Raw data present":    all(f.exists() for f in REQUIRED_RAW_FILES),
        "Python version":      sys.version.split()[0],
        "Platform":            sys.platform,
    }


def log_diagnostics(prefix: str = "") -> None:
    for key, value in get_diagnostics().items():
        log.info(f"{prefix}{key}: {value}")


def check_db() -> bool:
    """Return True if a usable warehouse file already exists on disk."""
    try:
        return DB_PATH.exists() and DB_PATH.is_file() and DB_PATH.stat().st_size > 0
    except OSError:
        return False


def _ensure_source_data() -> None:
    missing = [f for f in REQUIRED_RAW_FILES if not f.exists()]
    if not missing:
        return
    log.info("Generating source data …")
    _ensure_python_on_path()
    try:
        from generate_data import generate
        generate(root=ROOT)
    except Exception as exc:
        raise BootstrapError("generate_source_data", exc) from exc

    still_missing = [f for f in REQUIRED_RAW_FILES if not f.exists()]
    if still_missing:
        raise BootstrapError(
            "generate_source_data",
            FileNotFoundError(f"Expected files still missing after generation: {still_missing}"),
        )


def _run_pipeline(tmp_path: Path) -> None:
    log.info("Executing analytics pipeline …")
    _ensure_python_on_path()
    try:
        from run_pipeline import run as run_pipeline
        run_pipeline(db_path=tmp_path)
    except Exception as exc:
        raise BootstrapError("execute_pipeline", exc) from exc


def build_db_if_missing() -> None:
    """
    Build the DuckDB warehouse if it doesn't already exist, then verify the
    result. Safe — and cheap — to call on every app startup/rerun: it is a
    no-op (single stat() call) once the file is present.

    Enforced order:
        1. check  — does the file already exist?
        2. build  — generate source data + run the SQL pipeline if not
        3. verify — re-check the file exists and is non-empty after building
    Raises BootstrapError with a specific step name on any failure, including
    if the file is still missing after a build that reported success — this
    must never be allowed to fall through silently to a read-only connect.
    """
    log.info("Bootstrap started.")
    log_diagnostics("  ")

    if check_db():
        log.info("Warehouse already present — skipping build.")
        log.info("Bootstrap completed.")
        return

    log.info("Database not found. Building warehouse …")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Build into a temp file in the SAME directory as DB_PATH (never /tmp —
    # an os.replace() across filesystems raises EXDEV), then atomically move
    # it into place, so a crash mid-build never leaves a partial/corrupt file
    # that check_db() would mistake for a ready warehouse.
    tmp_path = DB_PATH.with_name(DB_PATH.name + ".building")
    if tmp_path.exists():
        tmp_path.unlink()

    try:
        _ensure_source_data()
        _run_pipeline(tmp_path)

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            raise BootstrapError(
                "execute_pipeline",
                RuntimeError("Pipeline reported success but produced no database file."),
            )

        tmp_path.replace(DB_PATH)
    except BootstrapError:
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        raise BootstrapError("unknown", exc) from exc

    # Verify — never trust a "no exception raised" signal on its own.
    if not check_db():
        raise BootstrapError(
            "verify_db",
            FileNotFoundError(
                f"Build completed without error but {DB_PATH} is still missing or empty."
            ),
        )

    log.info("Warehouse ready.")
    log.info("Bootstrap completed.")
