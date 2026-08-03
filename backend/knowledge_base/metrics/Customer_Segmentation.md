---
metric: Customer Segmentation
category: Revenue
difficulty: Intermediate
tags: [SaaS, Subscription, KPI, Analytics]
---

# Customer Segmentation — Revenue Analytics

## Definition

Customer Segmentation in SaaS revenue analytics is the practice of splitting the customer base into meaningful groups (by size, plan, industry, cohort, region, acquisition channel, health score, etc.) so that metrics like MRR, churn, NRR, CAC, and LTV can be interpreted and acted on separately. Blended averages often hide the real drivers of growth and risk.

## Formula

There is no single formula; segmentation applies standard metrics within each segment:

**Formula**
Metric_segment = Metric calculated only on customers in segment S


Examples:

NRR_enterprise = Ending ARR_enterprise_cohort / Beginning ARR_enterprise_cohort
CAC_channel    = S&M_channel / New customers_channel
Churn_plan     = Customers lost_plan / Customers start_plan

Common segment dimensions:

- Firmographic: SMB / Mid-Market / Enterprise (employees or ARR tiers)
- Commercial: plan, billing interval, contract length
- Behavioral: usage intensity, feature adoption, support tickets
- Lifecycle: tenure cohort, trial-converted vs sales-assisted
- Geo / industry / channel

## Business Interpretation

Segmentation turns vanity blended KPIs into decisions. Enterprise may have low logo churn but long CAC payback; SMB may convert cheaply but churn fast. Pricing, packaging, CS coverage, and marketing budget should differ by segment. A practical operating cadence: review MRR bridge, NRR/GRR, and churn **by segment** every month, and assign owners to the segments that drive most ARR or most risk.

## Common Mistakes

- Using too many overlapping segments so every slice has tiny sample size.
- Segmenting only by vanity attributes that do not change decisions.
- Changing segment definitions over time without a migration map (breaks trends).
- Optimizing one segment’s CAC while hurting another segment’s retention.
- Reporting blended NRR only and missing that one segment is far below 100%.

## Interview Tips

**Q:** Which customer segments would you analyze first for a B2B SaaS revenue review?

**A:** Start with segments that explain revenue concentration and unit economics: ARR tier (e.g. <$5k / $5–50k / $50k+), plan, acquisition channel, and tenure cohort. Show MRR bridge and NRR/churn for each. Explain how findings change actions — e.g. cut paid spend to a high-churn SMB channel, or add CS capacity for mid-market accounts with strong expansion potential.

## SQL Example

## SQL Example (PostgreSQL)
-- MRR, customers, and ARPU by ARR-tier segment
WITH customer_mrr AS (
    SELECT
        customer_id,
        SUM(mrr) AS customer_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-06-01'
    GROUP BY customer_id
),
segmented AS (
    SELECT
        customer_id,
        customer_mrr,
        CASE
            WHEN customer_mrr < 500 THEN 'SMB'
            WHEN customer_mrr < 5000 THEN 'Mid-Market'
            ELSE 'Enterprise'
        END AS segment
    FROM customer_mrr
)
SELECT
    segment,
    COUNT(*) AS customers,
    SUM(customer_mrr) AS total_mrr,
    AVG(customer_mrr) AS arpu
FROM segmented
GROUP BY segment
ORDER BY total_mrr DESC;

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
