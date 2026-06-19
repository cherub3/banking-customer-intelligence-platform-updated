-- ══════════════════════════════════════════════════════════════════════
-- 03_segmentation.sql
-- Customer Segmentation: classify every customer into a business tier
-- Business question: Which customers deserve attention and why?
--
-- Segments (in order of priority):
--   VIP      — High-revenue, actively transacting relationship (£20K+/yr, 10+ txns/90d)
--   Growth   — Rising activity with meaningful revenue (growing trend)
--   At-Risk  — Activity or revenue is clearly declining (but not yet dormant)
--   Dormant  — No transactions in the last 90 days
--   Regular  — Stable, average engagement — no strong signal in either direction
--
-- Segment transitions (vs prior 90-day window):
--   Upgraded   — moved to a better tier (e.g. At-Risk → Regular)
--   Downgraded — moved to a worse tier  (e.g. Regular → At-Risk)
--   Stable     — same tier as before
--
-- Prior segment is estimated from the 90–180 day window so we can detect
-- which customers have improved or deteriorated since last quarter.
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_customer_segments;

INSERT INTO fct_customer_segments
WITH

-- ── Current segment: based on the most recent 90 days ────────────────
-- Decision matrix (each rule is checked in order — first match wins):
--
--   Dormant  : zero transactions in the last 90 days
--   VIP      : revenue ≥ £20K/year AND 10+ transactions/90 days
--   At-Risk  : clearly declining activity (≥3 prior txns, now ≤75% of that)
--   Growth   : genuinely growing activity AND meaningful revenue
--   Regular  : everyone else — stable, no strong signal
current_segment AS (
    SELECT
        customer_id,
        CASE
            WHEN txn_count_90d = 0
                THEN 'Dormant'

            WHEN revenue_ltm >= 20000 AND txn_count_90d >= 10
                THEN 'VIP'

            WHEN activity_trend IN ('Declining', 'Inactive')
             AND txn_count_prior_90d >= 3
                THEN 'At-Risk'

            WHEN activity_trend = 'Growing' AND revenue_ltm >= 800
                THEN 'Growth'

            ELSE 'Regular'
        END AS segment
    FROM fct_customer_360
),

-- ── Prior segment: estimated from the 90–180 day window ──────────────
-- Applying the same logic to the prior quarter's data tells us whether
-- a customer has improved or deteriorated since last period.
--
-- Note: prior_90d revenue is multiplied by 4 to produce an annualised
-- estimate comparable to the revenue_ltm threshold used for VIP.
prior_segment AS (
    SELECT
        customer_id,
        CASE
            WHEN txn_count_prior_90d = 0
                THEN 'Dormant'

            WHEN (revenue_prior_90d * 4) >= 20000
             AND txn_count_prior_90d >= 10
                THEN 'VIP'

            -- 1–2 transactions in the prior period = low engagement (At-Risk signal)
            WHEN txn_count_prior_90d BETWEEN 1 AND 2
                THEN 'At-Risk'

            ELSE 'Regular'
        END AS prior_segment
    FROM fct_customer_360
)

SELECT
    c.customer_id,
    DATE '2024-01-31'                                          AS snapshot_date,
    cs.segment,
    ps.prior_segment,

    -- Did this customer's tier improve or worsen since last quarter?
    CASE
        WHEN cs.segment = ps.prior_segment
            THEN 'Stable'

        -- Moving up to VIP or Growth from any lower tier
        WHEN cs.segment IN ('VIP', 'Growth')
         AND ps.prior_segment IN ('Regular', 'At-Risk', 'Dormant')
            THEN 'Upgraded'

        -- Recovering from At-Risk or Dormant back to Regular
        WHEN cs.segment = 'Regular'
         AND ps.prior_segment IN ('At-Risk', 'Dormant')
            THEN 'Upgraded'

        -- Falling into At-Risk or Dormant from a better tier
        WHEN cs.segment IN ('At-Risk', 'Dormant')
         AND ps.prior_segment IN ('VIP', 'Regular')
            THEN 'Downgraded'

        -- Slipping from VIP or Growth down to Regular (early warning)
        WHEN cs.segment = 'Regular'
         AND ps.prior_segment IN ('VIP', 'Growth')
            THEN 'Downgraded'

        ELSE 'Stable'
    END                                                        AS segment_change

FROM dim_customers    c
JOIN current_segment cs ON c.customer_id = cs.customer_id
JOIN prior_segment   ps ON c.customer_id = ps.customer_id;
