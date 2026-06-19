-- ══════════════════════════════════════════════════════════════════════
-- 09_views.sql
-- Dashboard-ready views: one view per dashboard page
-- Each view answers a specific business question for a specific audience.
--
--   v_executive_summary     → Executive Overview page   (CFO / Head of Relationship Banking)
--   v_customer_watchlist    → RM Workbook page          (Relationship Managers)
--   v_concentration_ladder  → Revenue Concentration page (Portfolio Risk team)
--   v_health_heatmap        → Health & Risk page         (Portfolio Managers)
--   v_exception_feed        → Exception Monitor page     (RM Operations)
-- ══════════════════════════════════════════════════════════════════════


-- ── View 1: Executive Summary ─────────────────────────────────────────
-- One-row summary of portfolio health for the executive dashboard header.
-- Includes both the KPI value and its business interpretation so the
-- dashboard can display "CRITICAL" next to the concentration percentage
-- without any Python-side logic.

DROP VIEW IF EXISTS v_executive_summary;

CREATE VIEW v_executive_summary AS
SELECT
    k.snapshot_date,

    -- Portfolio scale
    k.total_customers,
    k.active_customers,
    k.dormant_customers,
    ROUND(k.dormant_customers * 100.0 / k.total_customers, 1)          AS dormant_rate_pct,

    -- Health quality
    k.healthy_pct,
    k.critical_pct,
    CASE
        WHEN k.healthy_pct >= 50 THEN 'Strong'
        WHEN k.healthy_pct >= 30 THEN 'Moderate'
        ELSE                          'Weak'
    END                                                                  AS portfolio_health_rating,

    -- Concentration risk
    k.revenue_concentration_pct,
    c.revenue_dependency_score,
    ROUND(c.total_portfolio_revenue, 0)                                  AS portfolio_revenue_ltm,
    ROUND(c.scenario_top10_exit_risk, 0)                                 AS revenue_at_risk,

    -- Current quarter revenue (for QoQ comparison)
    ROUND(SUM(t.revenue_90d), 0)                                         AS revenue_current_90d,
    ROUND(SUM(t.revenue_prior_90d), 0)                                   AS revenue_prior_90d,
    ROUND(
        (SUM(t.revenue_90d) - SUM(t.revenue_prior_90d))
        / NULLIF(SUM(t.revenue_prior_90d), 0) * 100, 1
    )                                                                    AS revenue_qoq_pct,

    -- Action queue status
    k.open_retain_actions,
    k.open_crosssell_actions,
    k.open_reactivation_actions,
    (k.open_retain_actions + k.open_crosssell_actions + k.open_reactivation_actions)
                                                                         AS total_active_actions,

    -- Alerts
    k.open_exceptions,
    k.open_p1_exceptions,
    k.customers_at_risk

FROM fct_executive_kpis  k
JOIN fct_concentration   c ON k.snapshot_date = c.snapshot_date
JOIN fct_customer_360    t ON TRUE
GROUP BY
    k.snapshot_date, k.total_customers, k.active_customers, k.dormant_customers,
    k.healthy_pct, k.critical_pct, k.revenue_concentration_pct,
    c.revenue_dependency_score, c.total_portfolio_revenue, c.scenario_top10_exit_risk,
    k.open_retain_actions, k.open_crosssell_actions, k.open_reactivation_actions,
    k.open_exceptions, k.open_p1_exceptions, k.customers_at_risk;


-- ── View 2: Customer Watchlist (RM Workbook) ──────────────────────────
-- All customers with an active action, enriched with health, revenue,
-- and RM detail. Ordered by priority (P1 first) so RMs see their
-- most urgent customers at the top of the workbook.
-- Excludes Monitor (P4) — those require no active intervention.

DROP VIEW IF EXISTS v_customer_watchlist;

CREATE VIEW v_customer_watchlist AS
SELECT
    a.priority,
    a.sla_days,
    a.action_type,
    c.customer_name,
    a.customer_id,
    s.segment,
    h.health_category,
    h.health_trend,
    ROUND(h.health_score, 0)                                             AS health_score,
    ROUND(t.revenue_ltm, 0)                                              AS revenue_ltm,
    ROUND(t.revenue_90d, 0)                                              AS revenue_90d,
    ROUND(t.revenue_delta_pct, 1)                                        AS revenue_delta_pct,
    t.txn_count_90d,
    a.action_description,
    a.assigned_rm,
    c.region
FROM fct_rm_actions        a
JOIN dim_customers         c ON a.customer_id  = c.customer_id
JOIN fct_customer_segments s ON a.customer_id  = s.customer_id
JOIN fct_customer_health   h ON a.customer_id  = h.customer_id
JOIN fct_customer_360      t ON a.customer_id  = t.customer_id
WHERE a.action_type != 'Monitor'
ORDER BY
    CASE a.priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
    t.revenue_ltm DESC;


-- ── View 3: Revenue Concentration Ladder ──────────────────────────────
-- Every customer ranked by LTM revenue, showing individual and
-- cumulative revenue contribution. The "ladder" shows how quickly
-- revenue concentrates — executive can see in one scroll how many
-- customers account for 50%, 75%, and 90% of portfolio revenue.

DROP VIEW IF EXISTS v_concentration_ladder;

CREATE VIEW v_concentration_ladder AS
WITH customer_revenue AS (
    SELECT
        customer_id,
        ROUND(SUM(fee_revenue), 0) AS revenue_ltm
    FROM stg_transactions
    WHERE transaction_date >= '2023-02-01'
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue_ltm,
        ROW_NUMBER() OVER (ORDER BY revenue_ltm DESC)  AS revenue_rank,
        SUM(revenue_ltm) OVER ()                        AS total_revenue,
        SUM(revenue_ltm) OVER (ORDER BY revenue_ltm DESC
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                                                        AS cumulative_revenue
    FROM customer_revenue
)
SELECT
    r.revenue_rank,
    c.customer_name,
    r.customer_id,
    s.segment,
    h.health_category,
    h.health_trend,
    r.revenue_ltm,
    ROUND(r.revenue_ltm        / r.total_revenue * 100, 2) AS pct_of_portfolio,
    ROUND(r.cumulative_revenue / r.total_revenue * 100, 1) AS cumulative_pct,
    t.txn_count_90d,
    t.products_active
FROM ranked                r
JOIN dim_customers         c ON r.customer_id = c.customer_id
JOIN fct_customer_segments s ON r.customer_id = s.customer_id
JOIN fct_customer_health   h ON r.customer_id = h.customer_id
JOIN fct_customer_360      t ON r.customer_id = t.customer_id
ORDER BY r.revenue_rank;


-- ── View 4: Health Heatmap ─────────────────────────────────────────────
-- Segment × health category cross-tab for the portfolio health matrix.
-- Shows how health distributes across the five customer tiers.
-- Drives the heatmap chart on the Health & Risk dashboard page.

DROP VIEW IF EXISTS v_health_heatmap;

CREATE VIEW v_health_heatmap AS
SELECT
    s.segment,
    h.health_category,
    h.health_trend,
    COUNT(*)                                                             AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY s.segment), 1)
                                                                         AS pct_of_segment,
    ROUND(AVG(h.health_score), 1)                                        AS avg_health_score,
    ROUND(SUM(t.revenue_ltm), 0)                                         AS segment_revenue
FROM fct_customer_segments s
JOIN fct_customer_health   h ON s.customer_id = h.customer_id
JOIN fct_customer_360      t ON s.customer_id = t.customer_id
GROUP BY s.segment, h.health_category, h.health_trend
ORDER BY
    CASE s.segment
        WHEN 'VIP'     THEN 1
        WHEN 'Growth'  THEN 2
        WHEN 'Regular' THEN 3
        WHEN 'At-Risk' THEN 4
        ELSE                5
    END,
    CASE h.health_category
        WHEN 'Healthy'   THEN 1
        WHEN 'Watchlist' THEN 2
        WHEN 'At-Risk'   THEN 3
        ELSE                  4
    END;


-- ── View 5: Exception Feed ────────────────────────────────────────────
-- All open exceptions with customer detail, sorted by severity then
-- revenue impact. This is the live alert feed for the RM operations
-- team — the first thing checked every morning.

DROP VIEW IF EXISTS v_exception_feed;

CREATE VIEW v_exception_feed AS
SELECT
    e.severity,
    e.exception_type,
    e.customer_id,
    c.customer_name,
    s.segment,
    h.health_category,
    h.health_trend,
    ROUND(t.revenue_ltm, 0)                                              AS revenue_ltm,
    ROUND(t.revenue_90d, 0)                                              AS revenue_90d,
    ROUND(t.revenue_delta_pct, 1)                                        AS revenue_delta_pct,
    e.description,
    e.recommended_action,
    e.assigned_rm,
    e.detected_date,
    e.status
FROM fct_exceptions        e
JOIN dim_customers         c ON e.customer_id = c.customer_id
JOIN fct_customer_segments s ON e.customer_id = s.customer_id
JOIN fct_customer_health   h ON e.customer_id = h.customer_id
JOIN fct_customer_360      t ON e.customer_id = t.customer_id
WHERE e.status = 'OPEN'
ORDER BY
    CASE e.severity WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END,
    t.revenue_ltm DESC;
