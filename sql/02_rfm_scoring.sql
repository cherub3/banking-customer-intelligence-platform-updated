-- ══════════════════════════════════════════════════════════════════════
-- 02_rfm_scoring.sql
-- RFM Scoring: score every customer 1–5 on three business dimensions
-- Business question: How valuable and engaged is each customer?
--
-- Runs after 01_customer_360.sql and updates the RFM score columns.
--
-- R (Recency)   — When did this customer last transact?
-- F (Frequency) — How often do they transact (last 90 days)?
-- M (Monetary)  — How much fee revenue do they generate (last 12 months)?
--
-- Score 5 = best (most recent, most frequent, highest revenue)
-- Score 1 = worst (dormant, inactive, minimal revenue)
--
-- These scores feed directly into segmentation (03_segmentation.sql).
-- ══════════════════════════════════════════════════════════════════════


-- ── Recency Score ─────────────────────────────────────────────────────
-- How recently did the customer last transact?
--
--   Score 5 → last 14 days     (highly active)
--   Score 4 → last 15–30 days  (recently active)
--   Score 3 → last 31–60 days  (moderate engagement)
--   Score 2 → last 61–90 days  (low engagement)
--   Score 1 → 91+ days         (at risk of becoming dormant)

UPDATE fct_customer_360
SET rfm_recency_score = CASE
    WHEN days_since_last_txn <= 14  THEN 5
    WHEN days_since_last_txn <= 30  THEN 4
    WHEN days_since_last_txn <= 60  THEN 3
    WHEN days_since_last_txn <= 90  THEN 2
    ELSE                                 1
END;


-- ── Frequency Score ───────────────────────────────────────────────────
-- How many times did the customer transact in the last 90 days?
--
--   Score 5 → 50+ transactions   (high-volume corporate or SME client)
--   Score 4 → 25–49 transactions (active relationship)
--   Score 3 → 10–24 transactions (moderate usage)
--   Score 2 → 3–9 transactions   (low but present)
--   Score 1 → 0–2 transactions   (minimal engagement)

UPDATE fct_customer_360
SET rfm_frequency_score = CASE
    WHEN txn_count_90d >= 50 THEN 5
    WHEN txn_count_90d >= 25 THEN 4
    WHEN txn_count_90d >= 10 THEN 3
    WHEN txn_count_90d >= 3  THEN 2
    ELSE                          1
END;


-- ── Monetary Score ────────────────────────────────────────────────────
-- How much fee revenue has the customer generated in the last 12 months?
--
--   Score 5 → £20,000+/year   (major relationship — top clients)
--   Score 4 → £3,000–£19,999  (high-value client)
--   Score 3 → £800–£2,999     (mid-tier — growing potential)
--   Score 2 → £150–£799       (low value — regular retail)
--   Score 1 → under £150/year (minimal — review relationship cost)

UPDATE fct_customer_360
SET rfm_monetary_score = CASE
    WHEN revenue_ltm >= 20000 THEN 5
    WHEN revenue_ltm >= 3000  THEN 4
    WHEN revenue_ltm >= 800   THEN 3
    WHEN revenue_ltm >= 150   THEN 2
    ELSE                           1
END;
