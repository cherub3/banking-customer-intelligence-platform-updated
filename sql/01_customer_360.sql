-- ══════════════════════════════════════════════════════════════════════
-- 01_customer_360.sql
-- Customer 360: Complete value and behaviour profile per customer
-- Business question: What is the value and behaviour of each customer?
--
-- Period definitions (snapshot date: 2024-01-31):
--   LTM (last 12 months) : 2023-02-01 → 2024-01-31
--   Current 90 days      : 2023-11-03 → 2024-01-31
--   Prior 90 days        : 2023-08-05 → 2023-11-02
--
-- Comparing the current vs prior 90-day windows answers:
-- "Is this customer's relationship with us growing or deteriorating?"
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_customer_360;

INSERT INTO fct_customer_360
WITH

-- ── Fee income the bank earns from each customer, by time period ──────
revenue_by_period AS (
    SELECT
        customer_id,
        SUM(CASE WHEN transaction_date >= '2023-02-01'
                 THEN fee_revenue ELSE 0 END)                          AS revenue_ltm,
        SUM(CASE WHEN transaction_date >= '2023-11-03'
                 THEN fee_revenue ELSE 0 END)                          AS revenue_90d,
        SUM(CASE WHEN transaction_date BETWEEN '2023-08-05' AND '2023-11-02'
                 THEN fee_revenue ELSE 0 END)                          AS revenue_prior_90d
    FROM stg_transactions
    GROUP BY customer_id
),

-- ── How often and how much each customer transacts ────────────────────
activity_by_period AS (
    SELECT
        customer_id,
        COUNT(CASE WHEN transaction_date >= '2023-11-03'
                   THEN 1 END)                                         AS txn_count_90d,
        COUNT(CASE WHEN transaction_date BETWEEN '2023-08-05' AND '2023-11-02'
                   THEN 1 END)                                         AS txn_count_prior_90d,
        SUM(CASE WHEN transaction_date >= '2023-11-03'
                 THEN transaction_value ELSE 0 END)                    AS txn_volume_90d,
        MAX(transaction_date)                                          AS last_txn_date
    FROM stg_transactions
    GROUP BY customer_id
),

-- ── How many different products the customer actively uses ────────────
product_usage AS (
    SELECT
        customer_id,
        COUNT(DISTINCT product_id)                                     AS products_active
    FROM stg_transactions
    WHERE transaction_date >= '2023-11-03'
    GROUP BY customer_id
),

-- ── Which channel the customer prefers and how digital they are ───────
channel_usage AS (
    SELECT
        customer_id,
        COUNT(*)                                                       AS total_txns_90d,
        COUNT(CASE WHEN channel IN ('Online', 'Mobile') THEN 1 END)   AS digital_txns_90d,
        mode(channel)                                                  AS primary_channel
    FROM stg_transactions
    WHERE transaction_date >= '2023-11-03'
    GROUP BY customer_id
)

-- ── Combine all views into one row per customer ───────────────────────
SELECT
    c.customer_id,
    DATE '2024-01-31'                                                  AS snapshot_date,

    -- ── Revenue ────────────────────────────────────────────────────────
    COALESCE(r.revenue_ltm,       0)                                   AS revenue_ltm,
    COALESCE(r.revenue_90d,       0)                                   AS revenue_90d,
    COALESCE(r.revenue_prior_90d, 0)                                   AS revenue_prior_90d,

    -- Is this customer generating more or less revenue than last quarter?
    CASE
        WHEN COALESCE(r.revenue_prior_90d, 0) = 0
            THEN 0
        ELSE ROUND(
                (r.revenue_90d - r.revenue_prior_90d) / r.revenue_prior_90d * 100,
             2)
    END                                                                AS revenue_delta_pct,

    -- ── Transaction activity ───────────────────────────────────────────
    COALESCE(a.txn_count_90d,       0)                                 AS txn_count_90d,
    COALESCE(a.txn_count_prior_90d, 0)                                 AS txn_count_prior_90d,
    COALESCE(a.txn_volume_90d,      0)                                 AS txn_volume_90d,

    -- Are they transacting more or less often than last quarter?
    CASE
        WHEN COALESCE(a.txn_count_prior_90d, 0) = 0
            THEN 0
        ELSE ROUND(
                (a.txn_count_90d - a.txn_count_prior_90d)::DECIMAL
                / a.txn_count_prior_90d * 100,
             2)
    END                                                                AS txn_delta_pct,

    -- ── Product depth ──────────────────────────────────────────────────
    COALESCE(p.products_active, 0)                                     AS products_active,
    5                                                                  AS products_total,
    -- Customers using more products have deeper relationships (harder to churn)
    ROUND(COALESCE(p.products_active, 0) / 5.0 * 100, 1)             AS product_depth_pct,

    -- ── Channel behaviour ──────────────────────────────────────────────
    COALESCE(ch.primary_channel, 'None')                               AS primary_channel,
    -- High digital engagement = lower servicing cost + stronger product integration
    CASE
        WHEN COALESCE(ch.total_txns_90d, 0) = 0
            THEN 0
        ELSE ROUND(ch.digital_txns_90d::DECIMAL / ch.total_txns_90d * 100, 1)
    END                                                                AS digital_txn_pct,

    -- ── RFM scores (populated by 02_rfm_scoring.sql) ──────────────────
    0                                                                  AS rfm_recency_score,
    0                                                                  AS rfm_frequency_score,
    0                                                                  AS rfm_monetary_score,

    -- ── Recency ────────────────────────────────────────────────────────
    -- How many days since the customer last used any product?
    CASE
        WHEN a.last_txn_date IS NULL
            THEN 999
        ELSE DATEDIFF('day', a.last_txn_date, DATE '2024-01-31')
    END                                                                AS days_since_last_txn,

    -- ── Activity trend ─────────────────────────────────────────────────
    -- Requires at least 3 prior-period transactions for a decline to be flagged
    -- (avoids false alarms from customers with naturally low activity)
    CASE
        WHEN COALESCE(a.txn_count_90d, 0) = 0
            THEN 'Inactive'
        WHEN COALESCE(a.txn_count_prior_90d, 0) = 0
            THEN 'New'
        WHEN a.txn_count_90d >= a.txn_count_prior_90d * 1.10
            THEN 'Growing'
        WHEN a.txn_count_prior_90d >= 3
         AND a.txn_count_90d <= a.txn_count_prior_90d * 0.75
            THEN 'Declining'
        ELSE 'Stable'
    END                                                                AS activity_trend

FROM dim_customers          c
LEFT JOIN revenue_by_period  r  ON c.customer_id = r.customer_id
LEFT JOIN activity_by_period a  ON c.customer_id = a.customer_id
LEFT JOIN product_usage      p  ON c.customer_id = p.customer_id
LEFT JOIN channel_usage      ch ON c.customer_id = ch.customer_id;
