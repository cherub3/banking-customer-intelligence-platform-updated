-- ══════════════════════════════════════════════════════════════════════
-- 05_concentration.sql
-- Portfolio Concentration Analysis: revenue dependency risk
-- Business question: How dependent is the portfolio on a small number
-- of customers, and what revenue is at risk if they leave?
--
-- Outputs a single portfolio-level summary row with:
--   Revenue contribution: top 10, top 20, top 50 customers
--   Revenue Dependency Score: LOW / MEDIUM / HIGH / CRITICAL
--   Scenario analysis: revenue at risk if key customers exit
--
-- Revenue Dependency Score thresholds (top 10 contribution):
--   LOW      < 30%  — well-diversified portfolio
--   MEDIUM   30–39% — acceptable concentration
--   HIGH     40–49% — elevated risk, management attention required
--   CRITICAL 50%+   — severe concentration, executive escalation required
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_concentration;

WITH

-- ── Step 1: Total fee revenue per customer over the last 12 months ────
customer_revenue AS (
    SELECT
        customer_id,
        SUM(fee_revenue) AS revenue_ltm
    FROM stg_transactions
    WHERE transaction_date >= '2023-02-01'
    GROUP BY customer_id
),

-- ── Step 2: Rank every customer by revenue (highest first) ───────────
revenue_ranked AS (
    SELECT
        customer_id,
        revenue_ltm,
        ROW_NUMBER() OVER (ORDER BY revenue_ltm DESC) AS revenue_rank
    FROM customer_revenue
),

-- ── Step 3: Calculate top-tier revenue contributions ─────────────────
concentration AS (
    SELECT
        SUM(revenue_ltm)
            AS total_portfolio_revenue,

        SUM(CASE WHEN revenue_rank <= 10 THEN revenue_ltm ELSE 0 END)
            AS top_10_revenue,

        SUM(CASE WHEN revenue_rank <= 20 THEN revenue_ltm ELSE 0 END)
            AS top_20_revenue,

        SUM(CASE WHEN revenue_rank <= 50 THEN revenue_ltm ELSE 0 END)
            AS top_50_revenue
    FROM revenue_ranked
),

-- ── Step 4: Revenue at risk if Critical health customers exit ─────────
-- Critical customers are fully inactive — they represent revenue the
-- bank has already effectively lost if no reactivation occurs
critical_exit_risk AS (
    SELECT
        COALESCE(SUM(cr.revenue_ltm), 0) AS critical_revenue
    FROM customer_revenue cr
    JOIN fct_customer_health h ON cr.customer_id = h.customer_id
    WHERE h.health_category = 'Critical'
)

INSERT INTO fct_concentration
SELECT
    DATE '2024-01-31'                                                  AS snapshot_date,

    c.total_portfolio_revenue,

    -- Top 10 customer revenue and portfolio share
    ROUND(c.top_10_revenue, 2)                                         AS top_10_revenue,
    ROUND(c.top_10_revenue / NULLIF(c.total_portfolio_revenue, 0) * 100, 1)
                                                                       AS top_10_pct,

    -- Top 20 customer revenue and portfolio share
    ROUND(c.top_20_revenue, 2)                                         AS top_20_revenue,
    ROUND(c.top_20_revenue / NULLIF(c.total_portfolio_revenue, 0) * 100, 1)
                                                                       AS top_20_pct,

    -- Top 50 customer revenue and portfolio share
    ROUND(c.top_50_revenue, 2)                                         AS top_50_revenue,
    ROUND(c.top_50_revenue / NULLIF(c.total_portfolio_revenue, 0) * 100, 1)
                                                                       AS top_50_pct,

    -- Revenue Dependency Score: how concentrated is this portfolio?
    CASE
        WHEN c.top_10_revenue / NULLIF(c.total_portfolio_revenue, 0) >= 0.50 THEN 'CRITICAL'
        WHEN c.top_10_revenue / NULLIF(c.total_portfolio_revenue, 0) >= 0.40 THEN 'HIGH'
        WHEN c.top_10_revenue / NULLIF(c.total_portfolio_revenue, 0) >= 0.30 THEN 'MEDIUM'
        ELSE                                                                       'LOW'
    END                                                                AS revenue_dependency_score,

    -- Scenario 1: revenue exposed if top 10 customers exit
    ROUND(c.top_10_revenue, 2)                                         AS scenario_top10_exit_risk,

    -- Scenario 2: revenue already at risk from inactive (Critical) customers
    ROUND(r.critical_revenue, 2)                                       AS scenario_critical_exit_risk

FROM concentration c, critical_exit_risk r;
