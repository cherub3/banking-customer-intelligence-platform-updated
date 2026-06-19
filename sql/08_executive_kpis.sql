-- ══════════════════════════════════════════════════════════════════════
-- 08_executive_kpis.sql
-- Executive Portfolio KPIs: one row per snapshot, built for leadership
-- Business question: What is the state of the portfolio, and what matters?
--
-- Each metric is selected because it supports a specific decision:
--
--   total_customers / active_customers / dormant_customers
--     → How much of the portfolio is engaged vs inactive?
--
--   healthy_pct / critical_pct
--     → Is the overall portfolio health improving or eroding?
--
--   revenue_concentration_pct
--     → How dependent are we on a small number of clients?
--       Triggers escalation if top-10 share exceeds 40%.
--
--   open_retain_actions / open_crosssell_actions / open_reactivation_actions
--     → What is the RM team working on? Are we protecting, growing, or recovering?
--
--   customers_at_risk / revenue_at_risk
--     → How many customers are in At-Risk or Critical health,
--       and how much revenue is exposed if they exit?
--
--   open_exceptions / open_p1_exceptions
--     → How many alerts remain open? How many need CEO-level attention today?
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_executive_kpis;

INSERT INTO fct_executive_kpis
WITH

-- ── Portfolio health: customer-level counts and percentages ───────────
portfolio AS (
    SELECT
        COUNT(*)    AS total_customers,

        SUM(CASE WHEN s.segment != 'Dormant' THEN 1 ELSE 0 END)
            AS active_customers,

        SUM(CASE WHEN s.segment  = 'Dormant' THEN 1 ELSE 0 END)
            AS dormant_customers,

        ROUND(
            SUM(CASE WHEN h.health_category = 'Healthy'  THEN 1.0 ELSE 0 END)
            / COUNT(*) * 100, 1
        ) AS healthy_pct,

        ROUND(
            SUM(CASE WHEN h.health_category = 'Critical' THEN 1.0 ELSE 0 END)
            / COUNT(*) * 100, 1
        ) AS critical_pct,

        SUM(CASE WHEN h.health_category IN ('At-Risk', 'Critical') THEN 1 ELSE 0 END)
            AS customers_at_risk

    FROM fct_customer_segments s
    JOIN fct_customer_health   h ON s.customer_id = h.customer_id
),

-- ── RM workbook: count open actions by type ───────────────────────────
rm_summary AS (
    SELECT
        SUM(CASE WHEN action_type = 'Retain'     THEN 1 ELSE 0 END)
            AS open_retain_actions,

        SUM(CASE WHEN action_type = 'Cross-Sell' THEN 1 ELSE 0 END)
            AS open_crosssell_actions,

        SUM(CASE WHEN action_type = 'Reactivate' THEN 1 ELSE 0 END)
            AS open_reactivation_actions

    FROM fct_rm_actions
    WHERE status = 'OPEN'
),

-- ── Exception monitor: total open alerts and P1 count ─────────────────
exception_summary AS (
    SELECT
        COUNT(*)    AS open_exceptions,

        SUM(CASE WHEN severity = 'P1' THEN 1 ELSE 0 END)
            AS open_p1_exceptions

    FROM fct_exceptions
    WHERE status = 'OPEN'
)

-- ── Final row: one record per portfolio snapshot ──────────────────────
SELECT
    DATE '2024-01-31'            AS snapshot_date,

    -- Portfolio headcount
    p.total_customers,
    p.active_customers,
    p.dormant_customers,

    -- Health quality
    p.healthy_pct,
    p.critical_pct,

    -- Concentration risk (source: 05_concentration.sql)
    c.top_10_pct                 AS revenue_concentration_pct,

    -- RM workbook totals
    r.open_retain_actions,
    r.open_crosssell_actions,
    r.open_reactivation_actions,

    -- Revenue risk
    p.customers_at_risk,
    c.scenario_top10_exit_risk   AS revenue_at_risk,

    -- Exception alerts
    e.open_exceptions,
    e.open_p1_exceptions

FROM portfolio         p
   , rm_summary        r
   , exception_summary e
   , fct_concentration c;
