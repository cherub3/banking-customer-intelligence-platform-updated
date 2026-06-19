# Key Findings
## Banking Customer Intelligence Platform — January 2024 Analysis

*These findings are generated from 152,502 transactions across 1,000 customer relationships,
analysed using the 9-layer SQL pipeline. Every number is derived directly from the data.*

---

## Finding 1: Revenue Concentration is CRITICAL — 10 Clients Control 51.4% of the Portfolio

The portfolio's Revenue Dependency Score is **CRITICAL**, the highest severity rating. The top 10 customers by LTM fee revenue — all classified as VIP — generate **£879,206 out of £1,711,764 total portfolio revenue**, representing **51.4% of all income** from just **1.0% of the customer base**.

The concentration does not taper gradually. Customer ranked 10th (Palmer Group) contributes £76,573 per year. Customer ranked 11th (Clarke Group) contributes £5,735 — a **13-fold drop** between consecutive ranks. Revenue above rank 10 is institutional; revenue below rank 10 is retail-scale. There is no mid-market buffer.

**Scenario analysis:** If the top 10 clients were to exit simultaneously, **£879,206 in annual revenue** would disappear — equivalent to the bank needing to onboard and grow **153 new Regular-tier customers** to break even. The scenario is extreme but the sensitivity is real: even a partial VIP exit creates disproportionate revenue loss.

**Top 10 Revenue Contribution:**

| Rank | Customer | LTM Revenue | % of Portfolio | Cumulative % |
|---|---|---|---|---|
| 1 | Fisher Ltd | £97,338 | 5.69% | 5.7% |
| 2 | Young, Evans and Lucas | £94,732 | 5.53% | 11.2% |
| 3 | Evans LLC | £94,396 | 5.51% | 16.7% |
| 4 | Robinson-Davis | £92,984 | 5.43% | 22.2% |
| 5 | Pritchard, Thomas and Nicholls | £88,512 | 5.17% | 27.3% |
| 6 | Lee, Marsden and Evans | £87,073 | 5.09% | 32.4% |
| 7 | Thomas and Sons | £84,301 | 4.92% | 37.3% |
| 8 | Phillips, Cross and Miah | £81,700 | 4.77% | 42.1% |
| 9 | Simpson Group | £81,596 | 4.77% | 46.9% |
| 10 | Palmer Group | £76,573 | 4.47% | 51.4% |

**Implication:** Revenue concentration at this level is a single point of failure, not a diversification strategy. The portfolio requires a structural diversification programme targeting a MEDIUM rating (top-10 share below 40%).

---

## Finding 2: Four P1 Alerts — VIP Clients Showing Active Revenue Decline

Despite all 10 VIP clients being classified as **Healthy** in their overall health score (all scoring 98–99.9/100), the exception monitor detected **4 Priority 1 revenue decline alerts** on VIP-tier clients. These customers have not yet deteriorated in aggregate health metrics, but their **quarter-on-quarter fee revenue has fallen 22–29%**.

| Customer | LTM Revenue | Current 90d | Prior 90d | Revenue Change |
|---|---|---|---|---|
| Evans LLC | £94,396 | £20,422 | £26,412 | **−22.7%** |
| Lee, Marsden and Evans | £87,073 | £17,562 | £24,737 | **−29.0%** |
| Thomas and Sons | £84,301 | £18,259 | £23,570 | **−22.5%** |
| Palmer Group | £76,573 | £17,439 | £23,196 | **−24.8%** |

**Combined:** These four clients earned £73,682 in the current quarter versus £97,915 in the prior quarter — a **£24,233 shortfall (−24.8%)** on just four relationships.

The health score does not yet reflect this decline because the composite metric includes activity and engagement dimensions that remain strong. This is a known limitation of lagging composite scores: revenue deterioration can be 30–60 days ahead of health score deterioration. The exception monitor catches it early.

**Implication:** These 4 clients represent the highest-priority relationship management task in the portfolio. The cause of the revenue decline is unknown from the data — it could be seasonality, a product switch, a competitor offering, or the start of a relationship exit. Senior RM contact within 24 hours is required to determine which.

---

## Finding 3: Portfolio Revenue Declined 3.4% Quarter-on-Quarter

Portfolio fee revenue fell from **£421,020 in the prior 90 days** to **£406,840 in the current 90 days**, a decline of **−3.4% (−£14,180)**. This is the first negative quarter in the review cycle.

The decline is broad-based, not concentrated. Revenue decline of 20% or more was recorded across **420 customers** in the current quarter, distributed as:

- **At-Risk segment:** 204 customers, average decline −45.8%, worst case −86.7%
- **Dormant segment:** 133 customers, revenue fell to zero (−100%)
- **Regular segment:** 77 customers, average decline −28.4%, worst case −66.9%
- **VIP segment:** 4 customers, average decline −24.8% (the P1 exception group)
- **Growth segment:** 2 customers, average decline −60.4%

The bulk of the revenue decline is structural — it comes from the At-Risk and Dormant segments where customers are disengaging. However, the VIP contribution to the decline is disproportionately significant given its revenue weight.

**Implication:** The QoQ decline should be monitored at the next snapshot. If the At-Risk and Dormant customers are not addressed, and if the VIP revenue decline accelerates, the portfolio will enter a compounding deterioration cycle.

---

## Finding 4: Portfolio Health is Weak — Over Half of Customers are on Watchlist

The portfolio health distribution as at January 2024:

| Health Category | Count | % of Portfolio | What It Means |
|---|---|---|---|
| Healthy | 289 | 28.9% | Strong relationship — retain and grow |
| Watchlist | 533 | 53.3% | Early warning — monitor closely |
| At-Risk | 38 | 3.8% | Active intervention required |
| Critical | 140 | 14.0% | Fully inactive — reactivation or write-off |

Over **82.9% of customers are not classified as Healthy**. The Watchlist category — where the majority sits — is not an emergency, but it is an early warning. Watchlist customers have health scores between 45 and 69 out of 100, indicating some level of declining activity or recency. Without intervention, Watchlist customers migrate into At-Risk over subsequent quarters.

Health trends compound this picture: **242 customers (24.2%)** are on a **Deteriorating** trend, meaning their composite health score declined by more than 5 points compared to the prior quarter. Only 196 (19.6%) are Improving.

**Average health scores by segment:**

| Segment | Avg Health Score | Customers Deteriorating |
|---|---|---|
| VIP | 99.3 / 100 | 0 |
| Growth | 81.4 / 100 | 1 |
| Regular | 69.1 / 100 | 29 |
| At-Risk | 55.9 / 100 | 79 |
| Dormant | 0.0 / 100 | 133 |

The VIP and Growth tiers are healthy. The deterioration is concentrated in the At-Risk and Dormant segments — the bottom two tiers are pulling the portfolio average down.

**Implication:** The RM team should concentrate effort on preventing Watchlist customers from migrating to At-Risk, which requires early outreach before health scores fall below the 45-point threshold.

---

## Finding 5: Early Warning Signal — 24 Healthy Customers are Already Deteriorating

The most actionable early warning in the portfolio: **24 customers classified as Healthy** (health score ≥70) are on a **Deteriorating health trend**. They have not yet crossed the Watchlist threshold, but their trajectory points downward.

| Segment | Count | Average LTM Revenue |
|---|---|---|
| Regular | 15 | £1,921 |
| At-Risk | 8 | £1,474 |
| Growth | 1 | £3,564 |

These 24 customers are invisible to standard health-category monitoring — they appear as Healthy and would not trigger a Retain or Review action without the trend detection. The exception monitor does not currently flag them (no exception type covers Healthy + Deteriorating). They represent a **preventive intervention opportunity**: a proactive RM call now costs nothing; waiting until they drop to Watchlist costs a Retain action.

**Implication:** Consider adding a "HEALTHY DETERIORATING" exception type to the monitor in the next review cycle, targeted at the Growth segment customer (higher revenue value) and any Regular customers with revenue above £2,000/year.

---

## Finding 6: 26.5% of the Portfolio Downgraded Since Last Quarter

Segment change analysis shows **265 customers (26.5%) were downgraded** to a worse tier compared to the prior 90-day period, against only 69 upgrades (6.9%). The remaining 666 customers (66.6%) were stable.

The downgrade flow predominantly runs from **Regular → At-Risk** (227 customers) and **Regular → Dormant** (38 customers). No VIP or Growth customers downgraded. The concentration of downgrades in the Regular tier suggests a segment-wide disengagement pattern rather than individual relationship issues.

**Implication:** The ratio of 3.8 downgrades per upgrade indicates the portfolio is contracting in quality, not just in individual customer health. A portfolio-wide view of the Regular segment — the largest tier at 55.4% of customers — may reveal a structural cause such as a product, channel, or pricing change that is accelerating disengagement.

---

## Finding 7: 140 Dormant Customers Represent a Reactivation Opportunity — But the Window is Closing

**140 customers (14.0%)** have made zero transactions in the last 90 days. Their health scores are all 0 — Critical. Their combined LTM fee revenue contribution is under **£2,000**, meaning they have effectively already churned.

The reactivation window for these customers is a function of how long they have been inactive. Customers dormant for 90–120 days are meaningfully more reachable than those inactive for 180+ days. The current dataset does not distinguish sub-groups within the Dormant tier, but the reactivation priority should be:

1. **Newly dormant** (became dormant in the last 30 days) — highest reactivation probability
2. **Dormant with prior Watchlist classification** — had some engagement recently
3. **Long-term dormant** — lowest probability, may be candidates for account review

**Implication:** The 140 Reactivation P3 actions (SLA 7 days) should be triaged by time-since-last-transaction before outreach. Contacting all 140 with the same message will yield low return. A tiered reactivation script with product-specific offers for recently dormant customers will produce the best recovery rate.

---

*Analysis generated by: Banking Customer Intelligence & Risk Analytics Platform*
*Data period: LTM 1 Feb 2023 – 31 Jan 2024 | Current quarter: 3 Nov 2023 – 31 Jan 2024*
*Source: 152,502 transactions | 1,000 customers | 9 analytical SQL layers*
