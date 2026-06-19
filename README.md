# Banking Customer Intelligence & Risk Analytics Pipeline

> End-to-end analytics platform built on 1,000 banking customers and 152,502 transactions — from raw data ingestion through a 9-layer SQL analytics engine to an executive-grade Streamlit dashboard.

---

## What This Project Demonstrates

| Capability | Implementation |
|---|---|
| Data Engineering | Synthetic banking data generation · DuckDB columnar storage |
| SQL Analytics | 9-layer incremental model: raw → staging → fact → KPI → views |
| Customer Analytics | RFM scoring · 5-segment model · 4-dimension health scoring |
| Risk Intelligence | Revenue concentration analysis · Automated exception detection · P1/P2/P3 alert feed |
| Dashboarding | 5-page Streamlit app · Plotly charts · Executive-grade UI |
| Business Storytelling | Management pack · RM action workbook · Portfolio-level insight narration |

---

## Dashboard Pages

### Executive Overview
Portfolio-level KPIs for the CFO and Head of Relationship Banking. Revenue LTM, active customer count, concentration risk (CRITICAL badge), P1 alert count, and revenue at risk — plus three Plotly donuts, a top-10 horizontal bar, and P1 exception cards.

### Customer Intelligence
Full 1,000-customer explorer with sidebar filters (Segment · Health · Trend · Action). Includes a health matrix heatmap (Segment × Health Category), revenue vs health scatter, and a sortable dataframe with progress bars.

### Risk & Exceptions
652 open exceptions across 5 types, with a P1 alert banner, grouped bar chart by exception type and severity, a severity donut, and a filterable full exception feed. P1 cards show each VIP client's revenue decline.

### RM Action Centre
Relationship Manager workbook: 1,000 prioritised actions (P1–P4), stacked bar chart by action type, action type definitions panel, and a filterable 500-row workbook sorted by priority.

### Management Pack
Pre-formatted monthly business review. Navy header block, 6 KPI cards, 4 key findings (colour-coded by severity), and a priority action agenda table — ready to screenshot or print to PDF.

---

## Analytics Architecture

```
Raw Data (Synthetic)
    └── 01_raw_transactions.sql       152,502 transactions · 1,000 customers
    └── 02_raw_customers.sql          Customer master · regions · assigned RMs

Staging
    └── 03_staging_transactions.sql   Clean · validated · type-cast

Facts
    └── 04_fct_customer_360.sql       RFM scores · revenue LTM · 90d · prior 90d
    └── 05_fct_customer_segments.sql  5-segment model (VIP/Growth/Regular/At-Risk/Dormant)
    └── 06_fct_customer_health.sql    4-dimension health score · trend detection

Intelligence
    └── 07_fct_exceptions.sql         5 exception types · P1/P2/P3 severity
    └── 08_fct_rm_actions.sql         RM workbook · priority · SLA · action type

Views (Dashboard Layer)
    └── 09_views.sql
        ├── v_executive_summary       Single-row KPI row for the overview page
        ├── v_customer_watchlist      All actionable customers with RM fields
        ├── v_concentration_ladder    Top-N customers ranked by revenue
        ├── v_health_heatmap          Segment × health category matrix
        └── v_exception_feed          Full exception log with recommended actions
```

---

## Key Findings (Portfolio: January 2024)

1. **Revenue Concentration: CRITICAL** — Top 10 clients generate 51.4% of all fee income (£879,206 of £1.71M LTM). The revenue cliff between rank #10 (£76,573) and rank #11 (£5,735) is 13×.

2. **P1 Alert: 4 VIP Revenue Declines** — Evans LLC (−22.7%), Lee Marsden and Evans (−29.0%), Thomas and Sons (−22.5%), Palmer Group (−24.8%). Combined quarterly revenue fell £24,233. All four are still classified as Healthy in overall health score — the exception engine detected this signal before the category-level report would have.

3. **Portfolio Revenue −3.4% QoQ** — Fee revenue fell from £421,020 to £406,840. The decline is broad-based: 140 dormant accounts, 204 At-Risk customers averaging −45.8% revenue change.

4. **Early Warning: 24 Healthy Customers Deteriorating** — These accounts are invisible to standard exception monitoring. Proactive RM contact now is significantly cheaper than retention action later.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Database | DuckDB 0.10 (in-process analytical engine) |
| Data Generation | Python · Faker · NumPy |
| Analytics | SQL (DuckDB dialect) · 9-layer model |
| Dashboard | Streamlit ≥1.32 · Plotly ≥5.18 |
| Charts | Plotly Graph Objects + Express |
| Language | Python 3.11 |

---

## Project Structure

```
banking-intelligence-pipeline/
├── data/
│   └── banking_platform.duckdb       Analytical database (auto-generated)
├── sql/
│   ├── 01_raw_transactions.sql
│   ├── 02_raw_customers.sql
│   ├── 03_staging_transactions.sql
│   ├── 04_fct_customer_360.sql
│   ├── 05_fct_customer_segments.sql
│   ├── 06_fct_customer_health.sql
│   ├── 07_fct_exceptions.sql
│   ├── 08_fct_rm_actions.sql
│   └── 09_views.sql
├── scripts/
│   └── build_pipeline.py             Runs all SQL layers in sequence
├── dashboard/
│   ├── app.py                        Streamlit navigation router
│   ├── utils/
│   │   ├── db.py                     DB connection + query helpers
│   │   ├── styles.py                 Color system + HTML components
│   │   └── charts.py                 Plotly chart builders
│   └── pages/
│       ├── executive_overview.py
│       ├── customer_intelligence.py
│       ├── risk_exceptions.py
│       ├── rm_action_centre.py
│       └── management_pack.py
├── ARCHITECTURE.md
├── RESUME_ASSETS.md
└── README.md
```

---

## Quickstart

### Prerequisites

```bash
pip install duckdb streamlit plotly pandas faker numpy
```

### Build the Database

```bash
python scripts/build_pipeline.py
```

This runs all 9 SQL layers in sequence and writes `data/banking_platform.duckdb`.

### Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## Portfolio Context

Built to demonstrate banking analytics capabilities relevant to:
- **Business Analyst / Data Analyst** roles at Deutsche Bank, HSBC, Citi, JPMorgan, BNY, BlackRock
- Skills demonstrated: SQL data modelling, customer segmentation, risk analytics, executive dashboard design, business storytelling

> Data is 100% synthetic. Generated with Python Faker + NumPy seeded random — no real customer or transaction data is used.
