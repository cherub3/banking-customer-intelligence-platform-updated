-- ══════════════════════════════════════════════════════════════════════
-- 06_rm_actions.sql
-- RM Action Workbook: decision matrix for relationship managers
-- Business question: What should each RM do next, and how urgently?
--
-- Inputs:  customer segment (03_segmentation.sql)
--          customer health category + trend (04_health_scoring.sql)
--
-- Outputs per customer:
--   action_type        -- Retain / Review / Cross-Sell / Reactivate / Monitor
--   action_description -- Plain-language instruction for the RM
--   priority           -- P1 (24h) / P2 (3d) / P3 (7d) / P4 (30d)
--   sla_days           -- Numeric SLA in business days
--   assigned_rm        -- RM name from customer record
--
-- Decision matrix (first matching rule wins):
--
--   Segment    Health Category      Health Trend   → Action         Priority
--   ─────────  ──────────────────── ─────────────  ─────────────── ────────
--   Dormant    Any                  Any            Reactivate      P3
--   Any        Critical             Any            Retain          P1 / P2
--   VIP        Any                  Deteriorating  Retain          P1
--   Growth     Any                  Deteriorating  Retain          P1
--   VIP/Growth At-Risk              Any            Retain          P1 / P2
--   At-Risk    Any                  Deteriorating  Retain          P2
--   VIP/Growth Healthy/Watchlist    Stable/Imprv   Cross-Sell      P2 / P3
--   At-Risk    Any                  Stable/Imprv   Review          P3
--   Regular    Any                  Deteriorating  Review          P3
--   Else                                           Monitor         P4
-- ══════════════════════════════════════════════════════════════════════

DELETE FROM fct_rm_actions;

INSERT INTO fct_rm_actions
WITH

-- ── Step 1: Bring together segment, health, and RM assignment ─────────
customer_data AS (
    SELECT
        c.customer_id,
        c.relationship_manager,
        s.segment,
        h.health_category,
        h.health_trend
    FROM dim_customers        c
    JOIN fct_customer_segments s ON c.customer_id = s.customer_id
    JOIN fct_customer_health   h ON c.customer_id = h.customer_id
),

-- ── Step 2: Determine the recommended action for each customer ────────
-- Rules are ordered by business urgency: highest-risk situations first
with_action_type AS (
    SELECT
        customer_id,
        relationship_manager,
        segment,
        health_category,
        health_trend,

        CASE
            -- REACTIVATE: dormant customers regardless of anything else
            WHEN segment = 'Dormant'
                THEN 'Reactivate'

            -- RETAIN: critical health is always urgent
            WHEN health_category = 'Critical'
                THEN 'Retain'

            -- RETAIN: high-value customers showing deterioration
            WHEN segment IN ('VIP', 'Growth')
             AND (health_category = 'At-Risk' OR health_trend = 'Deteriorating')
                THEN 'Retain'

            -- CROSS-SELL: high-value customers who are stable and healthy
            WHEN segment IN ('VIP', 'Growth')
             AND health_category IN ('Healthy', 'Watchlist')
             AND health_trend IN ('Stable', 'Improving')
                THEN 'Cross-Sell'

            -- RETAIN: At-Risk segment is actively deteriorating
            WHEN segment = 'At-Risk'
             AND (health_category = 'At-Risk' OR health_trend = 'Deteriorating')
                THEN 'Retain'

            -- REVIEW: At-Risk segment but holding stable
            WHEN segment = 'At-Risk'
                THEN 'Review'

            -- REVIEW: any customer showing early deterioration
            WHEN health_trend = 'Deteriorating' OR health_category = 'At-Risk'
                THEN 'Review'

            -- CROSS-SELL: healthy regular customers who are improving
            WHEN segment = 'Regular'
             AND health_category = 'Healthy'
             AND health_trend = 'Improving'
                THEN 'Cross-Sell'

            -- MONITOR: stable, low-risk customers
            ELSE 'Monitor'
        END AS action_type

    FROM customer_data
),

-- ── Step 3: Assign priority based on action type and customer value ───
-- P1 = act within 24 hours (senior RM escalation)
-- P2 = act within 3 business days
-- P3 = act within 7 business days
-- P4 = standard 30-day review cycle
with_priority AS (
    SELECT
        customer_id,
        relationship_manager,
        segment,
        health_category,
        health_trend,
        action_type,

        CASE
            -- P1: VIP customers requiring retention are always highest priority
            WHEN action_type = 'Retain' AND segment = 'VIP'
                THEN 'P1'

            -- P1: Any customer in Critical health that is still deteriorating
            WHEN action_type = 'Retain'
             AND health_category = 'Critical'
             AND health_trend = 'Deteriorating'
                THEN 'P1'

            -- P1: Growth customers in active deterioration
            WHEN action_type = 'Retain'
             AND segment = 'Growth'
             AND health_trend = 'Deteriorating'
                THEN 'P1'

            -- P2: All other Retain actions (important but not immediate)
            WHEN action_type = 'Retain'
                THEN 'P2'

            -- P2: Review actions for VIP or Growth (early warning on valuable accounts)
            WHEN action_type = 'Review' AND segment IN ('VIP', 'Growth')
                THEN 'P2'

            -- P2: Cross-Sell for VIP (revenue opportunity not to miss)
            WHEN action_type = 'Cross-Sell' AND segment = 'VIP'
                THEN 'P2'

            -- P3: Reactivate, Review, Cross-Sell for non-VIP accounts
            WHEN action_type IN ('Reactivate', 'Review', 'Cross-Sell')
                THEN 'P3'

            -- P4: Monitor — no urgency
            ELSE 'P4'
        END AS priority

    FROM with_action_type
)

-- ── Final output: full action record for the RM workbook ──────────────
SELECT
    customer_id || '_2024-01-31'    AS action_id,
    customer_id,
    DATE '2024-01-31'               AS snapshot_date,
    segment,
    health_category,
    action_type,

    -- Plain-language instruction the RM can act on immediately
    CASE
        WHEN action_type = 'Retain' AND segment = 'VIP'
            THEN 'URGENT: Senior RM to call today. Review relationship health, confirm account status, and agree a retention plan before next business day.'

        WHEN action_type = 'Retain' AND segment = 'Growth'
            THEN 'Schedule RM call within 72 hours. Review product usage and revenue trend. Identify concerns before the relationship deteriorates further.'

        WHEN action_type = 'Retain' AND health_category = 'Critical'
            THEN 'Customer is fully inactive. Contact immediately to understand reason and offer re-engagement. Log all contact attempts.'

        WHEN action_type = 'Retain'
            THEN 'Activity or revenue is declining. Contact customer to understand concerns and present retention options before they disengage.'

        WHEN action_type = 'Cross-Sell' AND segment = 'VIP'
            THEN 'High-value customer is healthy and engaged. Prepare a tailored product proposal for the next scheduled RM call.'

        WHEN action_type = 'Cross-Sell'
            THEN 'Customer is healthy and growing. Present relevant product or service upgrade at next RM touchpoint.'

        WHEN action_type = 'Reactivate'
            THEN 'No transactions in 90+ days. Contact to understand reason for inactivity and offer a re-engagement incentive or product review.'

        WHEN action_type = 'Review'
            THEN 'Early warning signal detected. RM to review recent account activity. If decline is confirmed, escalate to Retain action immediately.'

        ELSE 'No immediate action required. Continue monitoring at standard review cadence.'
    END AS action_description,

    priority,

    -- SLA in business days (drives daily RM task list sorting)
    CASE priority
        WHEN 'P1' THEN 1
        WHEN 'P2' THEN 3
        WHEN 'P3' THEN 7
        ELSE            30
    END AS sla_days,

    relationship_manager  AS assigned_rm,
    'OPEN'                AS status

FROM with_priority;
