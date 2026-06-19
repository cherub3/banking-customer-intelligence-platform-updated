-- ══════════════════════════════════════════════════════════════════════
-- 04_health_scoring.sql
-- Customer Health Scoring: detect deterioration, not just classify
-- Business question: Is this customer relationship getting better or worse?
--
-- Each customer receives:
--   health_score     — composite 0–100 (higher = healthier relationship)
--   health_category  — Healthy / Watchlist / At-Risk / Critical
--   health_trend     — Improving / Stable / Deteriorating
--
-- The four health dimensions (each scored 0–100):
--   Activity Health   — how often is the customer transacting? (weight: 30%)
--   Revenue Health    — how much fee income are they generating? (weight: 35%)
--   Recency Health    — how recently did they last transact?    (weight: 25%)
--   Engagement Health — how many products? how digital?         (weight: 10%)
--
-- Revenue has the highest weight because revenue deterioration is the
-- primary business risk. Recency is the leading indicator of churn.
--
-- HOW HEALTH TREND WORKS:
--   Current score  = weighted average using last 90 days of data
--   Prior score    = same formula applied to the prior 90-day window
--   If current ≥ prior + 5 → Improving
--   If current ≤ prior - 5 → Deteriorating
--   Otherwise              → Stable
--
--   Using identical formulas for both periods ensures the comparison
--   is valid. A 5-point shift is meaningful; smaller changes are noise.
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_customer_health;

INSERT INTO fct_customer_health
WITH

-- ── Current period: dimension scores using last 90 days ───────────────
-- Each dimension uses a consistent scoring scale (0–100).
-- The same scale is applied to the prior period below.

current_scores AS (
    SELECT
        customer_id,

        -- Activity Health: how actively is this customer transacting?
        CASE
            WHEN txn_count_90d = 0   THEN 0    -- No activity at all
            WHEN txn_count_90d <= 2  THEN 20   -- Barely active
            WHEN txn_count_90d <= 9  THEN 45   -- Low engagement
            WHEN txn_count_90d <= 24 THEN 70   -- Moderate — typical retail customer
            WHEN txn_count_90d <= 49 THEN 85   -- High — strong relationship
            ELSE                          100  -- Very high — VIP/corporate client
        END AS activity_health,

        -- Revenue Health: how much fee income is this customer generating?
        -- Scored on absolute quarterly revenue to allow direct period comparison
        CASE
            WHEN revenue_90d = 0       THEN 0    -- No revenue at all
            WHEN revenue_90d <= 100    THEN 25   -- Minimal
            WHEN revenue_90d <= 400    THEN 50   -- Below average
            WHEN revenue_90d <= 2000   THEN 75   -- Above average
            ELSE                            100  -- Major client
        END AS revenue_health,

        -- Recency Health: when did this customer last transact?
        CASE
            WHEN days_since_last_txn <= 14  THEN 100  -- Active in last 2 weeks
            WHEN days_since_last_txn <= 30  THEN 85   -- Active this month
            WHEN days_since_last_txn <= 60  THEN 60   -- Active in last 2 months
            WHEN days_since_last_txn <= 90  THEN 35   -- Active this quarter (barely)
            ELSE                                  0   -- No activity in 90+ days
        END AS recency_health,

        -- Engagement Health: how embedded is this customer in the bank's products?
        -- Customers using more products and digital channels have deeper relationships
        -- and are significantly less likely to churn
        ROUND((product_depth_pct + digital_txn_pct) / 2.0, 1) AS engagement_health

    FROM fct_customer_360
),

-- ── Prior period: same dimension scores using the prior 90-day window ─
-- Applying identical scoring rules to prior-period data lets us compare
-- the two periods fairly and detect genuine trend changes.

prior_scores AS (
    SELECT
        customer_id,

        -- Prior Activity Health: same scoring, uses txn_count_prior_90d
        CASE
            WHEN txn_count_prior_90d = 0   THEN 0
            WHEN txn_count_prior_90d <= 2  THEN 20
            WHEN txn_count_prior_90d <= 9  THEN 45
            WHEN txn_count_prior_90d <= 24 THEN 70
            WHEN txn_count_prior_90d <= 49 THEN 85
            ELSE                                100
        END AS prior_activity_health,

        -- Prior Revenue Health: same scoring, uses revenue_prior_90d
        CASE
            WHEN revenue_prior_90d = 0       THEN 0
            WHEN revenue_prior_90d <= 100    THEN 25
            WHEN revenue_prior_90d <= 400    THEN 50
            WHEN revenue_prior_90d <= 2000   THEN 75
            ELSE                                  100
        END AS prior_revenue_health,

        -- Prior Recency Health: estimated from prior-period activity level
        -- We cannot compute exact days since last transaction for the prior period,
        -- so we use frequency as a proxy: more transactions → customer was more present
        CASE
            WHEN txn_count_prior_90d > 10 THEN 90   -- Frequently active: strong presence
            WHEN txn_count_prior_90d > 0  THEN 60   -- Occasionally active
            ELSE                               10   -- Absent: likely already drifting
        END AS prior_recency_health,

        -- Prior Engagement Health: product mix is relatively stable over 90 days,
        -- so we use the same engagement score as the current period
        ROUND((product_depth_pct + digital_txn_pct) / 2.0, 1) AS prior_engagement_health

    FROM fct_customer_360
),

-- ── Composite scores: weighted average of the four dimensions ─────────
-- Weights reflect business priority:
--   Revenue     35% — the primary measure of relationship value
--   Activity    30% — the leading indicator of engagement
--   Recency     25% — the earliest signal of customer drift
--   Engagement  10% — the stickiness factor (harder to churn multi-product customers)

composite_scores AS (
    SELECT
        c.customer_id,

        -- Individual dimension scores (stored for drill-down in the dashboard)
        c.activity_health,
        c.revenue_health,
        c.recency_health,
        c.engagement_health,

        -- Current composite score
        ROUND(
            c.activity_health   * 0.30 +
            c.revenue_health    * 0.35 +
            c.recency_health    * 0.25 +
            c.engagement_health * 0.10,
        1) AS health_score,

        -- Prior composite score (same weights)
        ROUND(
            p.prior_activity_health   * 0.30 +
            p.prior_revenue_health    * 0.35 +
            p.prior_recency_health    * 0.25 +
            p.prior_engagement_health * 0.10,
        1) AS prior_health_score

    FROM current_scores c
    JOIN prior_scores   p ON c.customer_id = p.customer_id
)

-- ── Final output: score + category + trend ────────────────────────────
SELECT
    customer_id,
    DATE '2024-01-31'  AS snapshot_date,

    activity_health,
    revenue_health,
    recency_health,
    engagement_health,
    health_score,

    -- What does this score mean for the business?
    CASE
        WHEN health_score >= 70 THEN 'Healthy'     -- Relationship is strong
        WHEN health_score >= 45 THEN 'Watchlist'   -- Monitor closely — early warning
        WHEN health_score >= 25 THEN 'At-Risk'     -- Intervention needed
        ELSE                         'Critical'    -- Urgent action required
    END AS health_category,

    -- Is this customer getting better or worse since last quarter?
    -- A 5-point shift is a meaningful change; anything smaller is noise
    CASE
        WHEN health_score >= prior_health_score + 5  THEN 'Improving'
        WHEN health_score <= prior_health_score - 5  THEN 'Deteriorating'
        ELSE                                              'Stable'
    END AS health_trend

FROM composite_scores;
