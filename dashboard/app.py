"""
app.py — Navigation router. Runs on every page load.
Start with: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from utils.styles import inject_css, C

st.set_page_config(
    page_title="Banking Intelligence Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure the warehouse exists before any page tries to query it. This runs on
# every script execution (app.py is the entry point for every page in this
# st.navigation app), but is cheap — a single os.stat() — once the database
# is built. Deliberately NOT wrapped in @st.cache_resource: see
# dashboard/utils/db.py module docstring for why that pattern hid the
# original Streamlit Cloud deployment failure.
from utils.db import ensure_warehouse  # noqa: E402

ensure_warehouse()

inject_css()

# ── Sidebar branding (persistent across all pages) ────────────────────────────
st.sidebar.markdown(
    f"""
    <div style="padding:0.25rem 0 1.25rem">
        <div style="font-size:1.05rem;font-weight:800;color:{C['navy']}">
            🏦 Banking Intelligence
        </div>
        <div style="font-size:0.72rem;color:{C['muted']};margin-top:0.15rem;letter-spacing:0.02em">
            Portfolio Analytics Platform
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Page registry ─────────────────────────────────────────────────────────────
pg = st.navigation(
    {
        "Portfolio": [
            st.Page("pages/executive_overview.py",    title="Executive Overview",    icon="📊"),
            st.Page("pages/customer_intelligence.py", title="Customer Intelligence", icon="👥"),
        ],
        "Operations": [
            st.Page("pages/risk_exceptions.py",  title="Risk & Exceptions", icon="⚠️"),
            st.Page("pages/rm_action_centre.py", title="RM Action Centre",  icon="📋"),
        ],
        "Reports": [
            st.Page("pages/management_pack.py", title="Management Pack", icon="📄"),
        ],
    }
)

# ── Sidebar debug panel (diagnostics — off by default) ────────────────────────
st.sidebar.markdown("---")
if st.sidebar.checkbox("🔧 Debug info", value=False):
    from bootstrap import get_diagnostics
    st.sidebar.json(get_diagnostics())

# ── Sidebar footer ────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div style="font-size:0.72rem;color:{C['muted']};line-height:1.7">
        <b>Snapshot:</b> 31 January 2024<br>
        <b>Customers:</b> 1,000<br>
        <b>Transactions:</b> 152,502<br>
        <b>Concentration:</b>
        <span style="color:{C['red']};font-weight:700">CRITICAL</span>
    </div>
    """,
    unsafe_allow_html=True,
)

pg.run()
