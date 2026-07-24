---
metric: CAC
category: Revenue
difficulty: Beginner
tags: [SaaS, Subscription, KPI, Growth]
---

# CAC — Customer Acquisition Cost

## Definition

Customer Acquisition Cost (CAC) is the average cost to acquire one new paying customer in a period. It includes sales and marketing spend (and often related overhead) divided by the number of new customers won. CAC is a core unit-economics input alongside LTV and payback period.

## Formula

```
CAC = Sales & Marketing Costs / Number of New Customers Acquired
```

Fully loaded variant (recommended for serious analysis):

```
CAC = (S&M salaries + ads + tools + agencies + commissions + related overhead)
      / New paying customers
```

Blended vs paid:

```
Blended CAC = Total S&M / All new customers
Paid CAC    = Paid acquisition spend / Customers from paid channels
```

## Business Interpretation

CAC shows how expensive growth is. Rising CAC can mean channel saturation, competitive pressure, or inefficient spend; falling CAC can mean better conversion, stronger brand, or product-led growth. CAC alone is incomplete — always compare it to LTV (`LTV:CAC`) and to CAC payback in months. Segment CAC by channel, segment, and geo: blended CAC can hide that enterprise is profitable while SMB paid ads are not.

## Common Mistakes

- Excluding sales salaries, commissions, or marketing tools from “fully loaded” CAC.
- Dividing by trials or signups instead of paying customers.
- Ignoring delayed attribution (spend in month N closes in month N+2).
- Using blended CAC for channel decisions that need paid/organic splits.
- Comparing CAC across companies with very different sales motions (PLG vs enterprise field sales).

## Interview Tips

**Q:** How would you calculate CAC for a SaaS company with a 3-month sales cycle?

**A:** Prefer a cohort or lagged approach: attribute sales & marketing spend to the period when opportunities were created (or use a consistent lag, e.g. spend in months T−2..T matches closes in month T), then divide by new paying customers closed. State your attribution window clearly. Also report blended vs channel CAC and note whether costs are fully loaded.

## SQL Example

```sql
-- Monthly blended CAC (assumes finance exports S&M spend by month)
WITH new_customers AS (
    SELECT
        DATE_TRUNC('month', first_paid_date) AS cohort_month,
        COUNT(DISTINCT customer_id) AS new_customers
    FROM customers
    WHERE first_paid_date IS NOT NULL
    GROUP BY 1
),
sm_spend AS (
    SELECT
        DATE_TRUNC('month', spend_date) AS spend_month,
        SUM(amount) AS sm_cost
    FROM sales_marketing_costs
    GROUP BY 1
)
SELECT
    n.cohort_month,
    s.sm_cost,
    n.new_customers,
    s.sm_cost / NULLIF(n.new_customers, 0) AS cac
FROM new_customers n
JOIN sm_spend s ON n.cohort_month = s.spend_month
ORDER BY n.cohort_month;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
