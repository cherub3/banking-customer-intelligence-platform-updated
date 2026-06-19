-- ══════════════════════════════════════════════════════════════════════
-- 07_exceptions.sql
-- Exception Monitor: operational alerts for immediate RM attention
-- Business question: Which customers need urgent action right now?
--
-- Detects five exception types (UNION ALL — one row per alert per customer):
--
--   1. CRITICAL CUSTOMER      — health score = 0, fully inactive (140 customers)
--   2. VIP DETERIORATING      — VIP or Growth segment with Deteriorating trend
--   3. REVENUE DECLINE        — revenue fell 20%+ vs prior quarter
--   4. ACTIVITY CLIFF         — transaction count fell 40%+ vs prior quarter
--   5. SEGMENT DOWNGRADE      — customer recently moved to Dormant or At-Risk
--
-- Severity:
--   P1 — act within 24 hours (VIP or high-value customers in acute distress)
--   P2 — act within 3 business days (meaningful revenue or segment risk)
--   P3 — act within 7 business days (early warning, monitor and assess)
--
-- A single customer can generate multiple exceptions (e.g., Revenue Decline
-- AND Activity Cliff). Each alert is a separate, actionable ticket for the RM.
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_exceptions;

INSERT INTO fct_exceptions
WITH

-- ── Join all analytical tables into one customer profile view ─────────
customer_profile AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.relationship_manager,
        s.segment,
        s.segment_change,
        s.prior_segment,
        h.health_category,
        h.health_trend,
        h.health_score,
        t.revenue_90d,
        t.revenue_prior_90d,
        t.revenue_delta_pct,
        t.txn_count_90d,
        t.txn_count_prior_90d,
        t.txn_delta_pct
    FROM dim_customers         c
    JOIN fct_customer_segments s ON c.customer_id = s.customer_id
    JOIN fct_customer_health   h ON c.customer_id = h.customer_id
    JOIN fct_customer_360      t ON c.customer_id = t.customer_id
)

-- ── Exception 1: Critical Customer ───────────────────────────────────
-- Health score = 0: the customer has made zero transactions in 90+ days.
-- This is the maximum health deterioration. Every Critical customer is an
-- immediate reactivation risk — the bank is generating zero revenue from them.
-- Severity P1 for VIP/Growth (lost value is high); P2 for all others.
SELECT
    'EXC_CRIT_' || customer_id      AS exception_id,
    customer_id,
    DATE '2024-01-31'               AS detected_date,
    'CRITICAL CUSTOMER'             AS exception_type,
    'Customer health score is 0. No transactions recorded in the last 90 days. Bank is generating zero fee revenue from this relationship.'
                                    AS description,
    CASE WHEN segment IN ('VIP', 'Growth') THEN 'P1' ELSE 'P2' END
                                    AS severity,
    'Contact customer immediately. Understand reason for inactivity and offer re-engagement. Log all contact attempts for escalation.'
                                    AS recommended_action,
    relationship_manager            AS assigned_rm,
    'OPEN'                          AS status
FROM customer_profile
WHERE health_category = 'Critical'

UNION ALL

-- ── Exception 2: VIP or Growth Deteriorating ─────────────────────────
-- A high-value customer whose health trend is Deteriorating represents
-- significant revenue risk. Early intervention is far cheaper than retention.
-- Excludes Critical (already caught by Exception 1).
SELECT
    'EXC_VIPDET_' || customer_id    AS exception_id,
    customer_id,
    DATE '2024-01-31'               AS detected_date,
    'VIP DETERIORATING'             AS exception_type,
    'High-value customer (' || segment || ') is showing a deteriorating health trend. Revenue and activity metrics have declined vs prior quarter.'
                                    AS description,
    CASE WHEN segment = 'VIP' THEN 'P1' ELSE 'P2' END
                                    AS severity,
    'Senior RM to review relationship immediately. Identify root cause of deterioration and schedule a retention call within SLA.'
                                    AS recommended_action,
    relationship_manager            AS assigned_rm,
    'OPEN'                          AS status
FROM customer_profile
WHERE segment IN ('VIP', 'Growth')
  AND health_trend = 'Deteriorating'
  AND health_category != 'Critical'

UNION ALL

-- ── Exception 3: Revenue Decline ─────────────────────────────────────
-- Revenue fell by more than 20% compared to the prior 90-day window.
-- This is an early revenue attrition signal — the customer is reducing
-- product usage or moving business to a competitor.
-- Only fires for customers with meaningful prior revenue (> £0).
-- Excludes Critical customers (already caught by Exception 1).
SELECT
    'EXC_REVDEC_' || customer_id    AS exception_id,
    customer_id,
    DATE '2024-01-31'               AS detected_date,
    'REVENUE DECLINE'               AS exception_type,
    'Fee revenue declined ' || CAST(ABS(ROUND(revenue_delta_pct, 0)) AS VARCHAR) || '% vs prior quarter. Current 90-day revenue: £' || CAST(ROUND(revenue_90d, 0) AS VARCHAR) || '.'
                                    AS description,
    CASE
        WHEN segment = 'VIP'                          THEN 'P1'
        WHEN segment = 'Growth' OR revenue_delta_pct <= -40 THEN 'P2'
        ELSE                                               'P3'
    END                             AS severity,
    'Review recent transaction activity. Contact customer to understand revenue decline and present options to restore product usage.'
                                    AS recommended_action,
    relationship_manager            AS assigned_rm,
    'OPEN'                          AS status
FROM customer_profile
WHERE revenue_delta_pct <= -20
  AND revenue_prior_90d > 0
  AND health_category != 'Critical'

UNION ALL

-- ── Exception 4: Activity Cliff ───────────────────────────────────────
-- Transaction count fell by 40%+ vs prior 90 days.
-- Sudden drops in transaction activity are the earliest indicator of
-- customer disengagement — often precede revenue decline by 30–60 days.
-- Only fires for customers who had meaningful prior activity (5+ txns).
-- Excludes Critical customers (already caught by Exception 1).
SELECT
    'EXC_CLIFF_' || customer_id     AS exception_id,
    customer_id,
    DATE '2024-01-31'               AS detected_date,
    'ACTIVITY CLIFF'                AS exception_type,
    'Transaction volume dropped ' || CAST(ABS(ROUND(txn_delta_pct, 0)) AS VARCHAR) || '% vs prior quarter. From ' || CAST(txn_count_prior_90d AS VARCHAR) || ' to ' || CAST(txn_count_90d AS VARCHAR) || ' transactions.'
                                    AS description,
    CASE
        WHEN segment = 'VIP'    THEN 'P1'
        WHEN segment = 'Growth' THEN 'P2'
        ELSE                         'P3'
    END                             AS severity,
    'Investigate sudden activity drop. Contact customer to confirm account is operating normally and log outcome in CRM.'
                                    AS recommended_action,
    relationship_manager            AS assigned_rm,
    'OPEN'                          AS status
FROM customer_profile
WHERE txn_delta_pct <= -40
  AND txn_count_prior_90d >= 5
  AND health_category != 'Critical'

UNION ALL

-- ── Exception 5: Segment Downgrade ───────────────────────────────────
-- Customer has been reclassified to a worse segment since last quarter.
-- Captures two meaningful downgrade scenarios:
--   a) Any customer who has become Dormant (revenue at zero)
--   b) Any At-Risk customer still deteriorating (risk of becoming Dormant)
-- Both require action before the customer slips to the next tier.
SELECT
    'EXC_DOWN_' || customer_id      AS exception_id,
    customer_id,
    DATE '2024-01-31'               AS detected_date,
    'SEGMENT DOWNGRADE'             AS exception_type,
    'Customer reclassified from ' || prior_segment || ' to ' || segment || '. Relationship quality has declined since last quarter.'
                                    AS description,
    CASE
        WHEN segment = 'Dormant' AND prior_segment IN ('VIP', 'Growth') THEN 'P1'
        WHEN segment = 'Dormant'                                         THEN 'P2'
        WHEN segment = 'At-Risk' AND health_trend = 'Deteriorating'      THEN 'P2'
        ELSE                                                                  'P3'
    END                             AS severity,
    'Review customer activity since reclassification. Assign a Retain or Reactivate action from the RM workbook and update status within SLA.'
                                    AS recommended_action,
    relationship_manager            AS assigned_rm,
    'OPEN'                          AS status
FROM customer_profile
WHERE segment_change = 'Downgraded'
  AND (
      segment = 'Dormant'
      OR (segment = 'At-Risk' AND health_trend = 'Deteriorating')
  );
