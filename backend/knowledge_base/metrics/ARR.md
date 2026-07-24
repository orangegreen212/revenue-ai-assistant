---
metric: ARR
category: Revenue
difficulty: Beginner
tags: [SaaS, Subscription, KPI]
---

# ARR — Annual Recurring Revenue

## Definition

Annual Recurring Revenue (ARR) is the yearly value of recurring subscription revenue. It is the annualized view of predictable subscription income and is the primary top-line metric used by SaaS companies, investors, and boards to track scale and growth.

## Formula

```
ARR = MRR × 12
```

From contracts directly:

```
ARR = Σ (annualized recurring fee for each active subscription)
```

Normalization examples:

```
Monthly plan ARR   = monthly fee × 12
Quarterly plan ARR = quarterly fee × 4
Multi-year deal ARR = total contract value / number of years
```

ARR bridge (period view):

```
Ending ARR = Beginning ARR + New ARR + Expansion ARR − Contraction ARR − Churned ARR
```

## Business Interpretation

ARR shows the size and trajectory of the recurring revenue base. Boards and investors use it to compare SaaS companies because it removes month-to-month noise and focuses on contracted recurring value. Rising ARR with healthy Net New ARR indicates scalable growth; ARR growth driven only by discounting or one-time annual prepayments can hide retention risk. Always pair ARR with NRR, churn, and CAC payback to judge growth quality.

## Common Mistakes

- Counting one-time professional services, implementation fees, or hardware as ARR.
- Treating the full multi-year contract value as ARR in year one instead of annualizing it.
- Mixing booked ARR, recognized revenue, and billings without clear labels.
- Including non-recurring usage overages as if they were guaranteed recurring revenue.
- Reporting ARR growth without showing churned and contracted ARR in the bridge.

## Interview Tips

**Q:** What is the difference between ARR and MRR, and when would you use each?

**A:** MRR is the monthly recurring run-rate; ARR is the same recurring base annualized (`ARR = MRR × 12`). Use MRR for operational monthly reporting, cohort bridges, and short-cycle SaaS. Use ARR for board decks, fundraising, annual planning, and enterprise deals with yearly contracts. Always be consistent about what is included (recurring only) and how annual/multi-year deals are normalized.

## SQL Example

```sql
-- ARR snapshot from active subscriptions (normalize all intervals to annual)
SELECT
    DATE_TRUNC('month', CURRENT_DATE) AS as_of_month,
    SUM(
        CASE billing_interval
            WHEN 'month' THEN amount * 12
            WHEN 'quarter' THEN amount * 4
            WHEN 'year' THEN amount
            ELSE NULL
        END
    ) AS total_arr
FROM subscriptions
WHERE status = 'active'
  AND (end_date IS NULL OR end_date > CURRENT_DATE);
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
