---
metric: Churn
category: Revenue
difficulty: Beginner
tags: [SaaS, Subscription, KPI, Retention]
---

# Churn — Customer & Revenue Churn

## Definition

Churn measures the rate at which customers or recurring revenue leave in a period. **Logo (customer) churn** counts accounts lost; **revenue churn** measures MRR/ARR lost to cancellations (and sometimes downgrades, depending on definition). Churn is the central retention risk metric for subscription businesses.

## Formula

Customer (logo) churn:

```
Logo Churn Rate = Customers lost in period / Customers at start of period
```

Revenue churn:

```
Revenue Churn Rate = Churned MRR in period / MRR at start of period
```

Gross vs net revenue churn:

```
Gross Revenue Churn = (Churned MRR + Contraction MRR) / Beginning MRR
Net Revenue Churn   = (Churned MRR + Contraction MRR − Expansion MRR) / Beginning MRR
```

Approximate lifetime:

```
Average lifetime (months) ≈ 1 / Monthly logo churn rate
```

## Business Interpretation

Low churn compounds growth: every point of churn reduction improves LTV, NRR, and forecast reliability. SMB products often see higher monthly logo churn; enterprise usually has lower logo churn but large revenue impact per lost account. Always separate voluntary churn (cancel) from involuntary churn (failed payments) — the fixes differ (product/CS vs dunning). Report churn by cohort, plan, and tenure; early-life churn often dominates.

## Common Mistakes

- Mixing logo churn and revenue churn in the same narrative without labels.
- Using end-of-period customer count as the denominator instead of starting count.
- Annualizing monthly churn incorrectly (`12 × monthly` overstates; prefer `1 − (1 − m)^12`).
- Counting downgrades as full churn (or ignoring them entirely).
- Hiding involuntary churn inside “total churn” without a payment-recovery view.

## Interview Tips

**Q:** What is the difference between logo churn and revenue churn? Which matters more?

**A:** Logo churn is the % of customers lost; revenue churn is the % of MRR/ARR lost. Revenue churn usually matters more for financial planning because losing one enterprise account can outweigh many SMB logos. Still track both: high logo churn with low revenue churn may mean SMB instability while the revenue base looks fine. Tie the answer to NRR/GRR when discussing revenue retention.

## SQL Example

```sql
-- Monthly logo churn and revenue churn
WITH start_customers AS (
    SELECT customer_id, mrr AS start_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
),
churned AS (
    SELECT c.customer_id, c.start_mrr
    FROM start_customers c
    LEFT JOIN mrr_snapshots e
      ON c.customer_id = e.customer_id
     AND e.snapshot_date = DATE '2026-02-01'
    WHERE e.customer_id IS NULL OR e.mrr = 0
)
SELECT
    (SELECT COUNT(*) FROM churned) * 1.0
        / NULLIF((SELECT COUNT(*) FROM start_customers), 0) AS logo_churn_rate,
    (SELECT SUM(start_mrr) FROM churned) * 1.0
        / NULLIF((SELECT SUM(start_mrr) FROM start_customers), 0) AS revenue_churn_rate;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
