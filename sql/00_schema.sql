-- ═══════════════════════════════════════════════════════════════════
-- 00_schema.sql
-- Banking Customer Intelligence Platform — Database Schema
-- Drop and recreate all tables. Safe to re-run.
-- ═══════════════════════════════════════════════════════════════════


-- ── Reference / Dimension Tables ────────────────────────────────────────────

DROP TABLE IF EXISTS dim_relationship_managers;
CREATE TABLE dim_relationship_managers (
    rm_id    VARCHAR(20) PRIMARY KEY,
    rm_name  VARCHAR(200),
    rm_grade VARCHAR(50),
    team     VARCHAR(100)
);

DROP TABLE IF EXISTS dim_products;
CREATE TABLE dim_products (
    product_id       VARCHAR(20) PRIMARY KEY,
    product_name     VARCHAR(200),
    product_category VARCHAR(100),   -- Payments | Deposits | Lending | Investments
    is_core_product  INTEGER         -- 1 = core, 0 = supplementary
);

DROP TABLE IF EXISTS dim_customers;
CREATE TABLE dim_customers (
    customer_id          VARCHAR(20) PRIMARY KEY,
    customer_name        VARCHAR(200),
    customer_type        VARCHAR(50),     -- Retail | SME | Corporate
    onboarding_date      DATE,
    relationship_manager VARCHAR(20),     -- FK to dim_relationship_managers.rm_id
    region               VARCHAR(100),
    is_active            INTEGER DEFAULT 1 -- 1 = active, 0 = inactive
);


-- ── Source / Staging Table ───────────────────────────────────────────────────

DROP TABLE IF EXISTS stg_transactions;
CREATE TABLE stg_transactions (
    transaction_id    VARCHAR(50) PRIMARY KEY,
    customer_id       VARCHAR(20),
    product_id        VARCHAR(20),
    transaction_date  DATE,
    transaction_type  VARCHAR(50),
    channel           VARCHAR(50),      -- Branch | Online | Mobile
    transaction_value DECIMAL(15, 2),   -- Customer transaction amount
    fee_revenue       DECIMAL(10, 2)    -- Bank's earned fee revenue
);


-- ── Analytical Fact Tables ───────────────────────────────────────────────────

DROP TABLE IF EXISTS fct_customer_360;
CREATE TABLE fct_customer_360 (
    customer_id          VARCHAR(20) PRIMARY KEY,
    snapshot_date        DATE,

    -- Revenue (bank's fee income from this customer)
    revenue_ltm          DECIMAL(15, 2),  -- Last 12 months
    revenue_90d          DECIMAL(15, 2),
    revenue_prior_90d    DECIMAL(15, 2),  -- 90–180 days ago
    revenue_delta_pct    DECIMAL(8,  4),  -- % change: 90d vs prior 90d

    -- Transaction activity
    txn_count_90d        INTEGER,
    txn_count_prior_90d  INTEGER,
    txn_volume_90d       DECIMAL(15, 2),  -- Total transaction value (not revenue)
    txn_delta_pct        DECIMAL(8,  4),  -- % change in transaction count

    -- Product usage
    products_active      INTEGER,
    products_total       INTEGER,         -- Total products in catalogue
    product_depth_pct    DECIMAL(5,  2),  -- products_active / products_total × 100

    -- Channel engagement
    primary_channel      VARCHAR(50),
    digital_txn_pct      DECIMAL(5,  2),  -- (Online + Mobile) / total × 100

    -- RFM scores
    rfm_recency_score    INTEGER,         -- 1 (worst) to 5 (best)
    rfm_frequency_score  INTEGER,
    rfm_monetary_score   INTEGER,

    -- Activity
    days_since_last_txn  INTEGER,
    activity_trend       VARCHAR(20)      -- Growing | Stable | Declining | Inactive
);

DROP TABLE IF EXISTS fct_customer_segments;
CREATE TABLE fct_customer_segments (
    customer_id    VARCHAR(20) PRIMARY KEY,
    snapshot_date  DATE,
    segment        VARCHAR(50),   -- VIP | Growth | Regular | At-Risk | Dormant
    prior_segment  VARCHAR(50),
    segment_change VARCHAR(20)    -- Upgraded | Downgraded | Stable | New
);

DROP TABLE IF EXISTS fct_customer_health;
CREATE TABLE fct_customer_health (
    customer_id       VARCHAR(20) PRIMARY KEY,
    snapshot_date     DATE,
    activity_health   DECIMAL(5, 2),  -- 0–100
    revenue_health    DECIMAL(5, 2),
    recency_health    DECIMAL(5, 2),
    engagement_health DECIMAL(5, 2),
    health_score      DECIMAL(5, 2),  -- Weighted composite 0–100
    health_category   VARCHAR(20),    -- Healthy | Watchlist | At-Risk | Critical
    health_trend      VARCHAR(20)     -- Improving | Stable | Deteriorating
);

DROP TABLE IF EXISTS fct_concentration;
CREATE TABLE fct_concentration (
    snapshot_date                DATE PRIMARY KEY,
    total_portfolio_revenue      DECIMAL(15, 2),
    top_10_revenue               DECIMAL(15, 2),
    top_10_pct                   DECIMAL(5,  2),
    top_20_revenue               DECIMAL(15, 2),
    top_20_pct                   DECIMAL(5,  2),
    top_50_revenue               DECIMAL(15, 2),
    top_50_pct                   DECIMAL(5,  2),
    revenue_dependency_score     VARCHAR(20),     -- LOW | MEDIUM | HIGH | CRITICAL
    scenario_top10_exit_risk     DECIMAL(15, 2),  -- Revenue lost if top 10 exit
    scenario_critical_exit_risk  DECIMAL(15, 2)   -- Revenue lost if Critical customers exit
);

DROP TABLE IF EXISTS fct_rm_actions;
CREATE TABLE fct_rm_actions (
    action_id          VARCHAR(50) PRIMARY KEY,
    customer_id        VARCHAR(20),
    snapshot_date      DATE,
    segment            VARCHAR(50),
    health_category    VARCHAR(20),
    action_type        VARCHAR(50),   -- Retain | Cross-Sell | Reactivate | Review | Monitor
    action_description TEXT,
    priority           VARCHAR(10),   -- P1 | P2 | P3 | P4
    sla_days           INTEGER,
    assigned_rm        VARCHAR(100),
    status             VARCHAR(20) DEFAULT 'OPEN'
);

DROP TABLE IF EXISTS fct_exceptions;
CREATE TABLE fct_exceptions (
    exception_id       VARCHAR(50) PRIMARY KEY,
    customer_id        VARCHAR(20),
    detected_date      DATE,
    exception_type     VARCHAR(100),
    description        TEXT,
    severity           VARCHAR(20),   -- P1 | P2 | P3
    recommended_action TEXT,
    assigned_rm        VARCHAR(100),
    status             VARCHAR(20) DEFAULT 'OPEN'
);

DROP TABLE IF EXISTS fct_executive_kpis;
CREATE TABLE fct_executive_kpis (
    snapshot_date             DATE PRIMARY KEY,
    -- Portfolio
    total_customers           INTEGER,
    active_customers          INTEGER,
    dormant_customers         INTEGER,
    healthy_pct               DECIMAL(5, 2),
    critical_pct              DECIMAL(5, 2),
    revenue_concentration_pct DECIMAL(5, 2),   -- Top 10 revenue %
    -- Relationship
    open_retain_actions       INTEGER,
    open_crosssell_actions    INTEGER,
    open_reactivation_actions INTEGER,
    -- Risk
    customers_at_risk         INTEGER,
    revenue_at_risk           DECIMAL(15, 2),
    open_exceptions           INTEGER,
    open_p1_exceptions        INTEGER
);
