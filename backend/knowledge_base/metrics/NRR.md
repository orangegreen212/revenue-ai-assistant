---
metric: NRR
category: Revenue
difficulty: Intermediate
tags: [SaaS, Subscription, KPI, Retention]
---

# NRR — Net Revenue Retention

## Definition

Net Revenue Retention (NRR), also called Net Dollar Retention (NDR), measures how recurring revenue from an existing customer cohort evolves over time after expansion, contraction, and churn. It answers: of the ARR/MRR we had from customers at the start of the period, how much do we still have from those same customers at the end — including upgrades and downgrades?

## Formula

```
NRR = (Beginning ARR + Expansion − Contraction − Churn) / Beginning ARR
```

Often expressed as a percentage:

```
NRR % = NRR × 100
```

Equivalent cohort form:

```
NRR = Ending ARR from starting cohort / Beginning ARR from starting cohort
```

Note: New logos acquired during the period are excluded from NRR; they belong in New ARR / logo growth metrics.

## Business Interpretation

NRR is one of the strongest signals of product-market fit and account expansion health. NRR above 100% means expansion from existing customers more than offsets churn and downgrades — the base grows even without new logos. Best-in-class B2B SaaS often targets 110–130%+ NRR. NRR below 100% means the existing base is shrinking and growth depends entirely on new acquisition. Segment NRR by plan, company size, and cohort to find where expansion or churn concentrates.

## Common Mistakes

- Including new customers acquired in the period in the NRR cohort.
- Using revenue recognition timing instead of subscription ARR/MRR for the cohort.
- Ignoring contraction (downgrades) and only subtracting full churn.
- Comparing NRR across companies without aligning on monthly vs trailing-twelve-month windows.
- Celebrating high NRR while logo churn is severe (few large expansions masking many lost accounts).

## Interview Tips

**Q:** What does NRR > 100% mean, and how is it different from GRR?

**A:** NRR > 100% means expansion revenue from the starting cohort exceeds losses from churn and contraction, so retained revenue grows. GRR (Gross Revenue Retention) excludes expansion and is capped at 100% — it only measures how much of the starting revenue you kept before upgrades. Use GRR for retention quality and NRR for net growth from the installed base.

## SQL Example

```sql
-- Simplified monthly NRR for a cohort of customers active at month start
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-02-01'
    GROUP BY customer_id
)
SELECT
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) AS nrr,
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) * 100 AS nrr_pct
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
