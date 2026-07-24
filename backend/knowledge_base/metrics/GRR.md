---
metric: GRR
category: Revenue
difficulty: Intermediate
tags: [SaaS, Subscription, KPI, Retention]
---

# GRR — Gross Revenue Retention

## Definition

Gross Revenue Retention (GRR), also called Gross Dollar Retention, measures how much recurring revenue from an existing customer cohort is retained after churn and contraction — **excluding** expansion. It isolates retention quality of the starting revenue base without credit for upsells.

## Formula

```
GRR = (Beginning ARR − Contraction − Churn) / Beginning ARR
```

As a percentage:

```
GRR % = GRR × 100
```

Relationship to NRR:

```
NRR = GRR + (Expansion / Beginning ARR)
```

GRR is capped at 100% because expansion is excluded.

## Business Interpretation

GRR answers whether you are keeping the revenue you already had. High GRR (often 85–95%+ annually for healthy B2B SaaS) means low churn and limited downgrades. Weak GRR with strong NRR can mean a few large expansions are masking broad retention problems. Product, CS, and finance teams use GRR to monitor account health independently of upsell motions. Track GRR by segment (SMB vs mid-market vs enterprise) because churn dynamics differ sharply by customer size.

## Common Mistakes

- Including expansion upside in GRR (that belongs in NRR only).
- Reporting GRR above 100% — by definition it cannot exceed 100%.
- Mixing logo retention with revenue retention without clarifying the metric.
- Using different cohort windows (monthly vs TTM) when benchmarking peers.
- Ignoring contraction from seat reductions and plan downgrades.

## Interview Tips

**Q:** Why can GRR never exceed 100%, while NRR can?

**A:** GRR only subtracts churn and contraction from beginning revenue; it gives no credit for upgrades or add-ons, so the best case is retaining 100% of the starting base. NRR adds expansion, so retained revenue can grow above the starting base and exceed 100%.

## SQL Example

```sql
-- Monthly GRR: retained MRR from starting cohort, excluding expansion upside
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
    SUM(LEAST(COALESCE(e.end_mrr, 0), b.begin_mrr))
        / NULLIF(SUM(b.begin_mrr), 0) AS grr,
    SUM(LEAST(COALESCE(e.end_mrr, 0), b.begin_mrr))
        / NULLIF(SUM(b.begin_mrr), 0) * 100 AS grr_pct
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
