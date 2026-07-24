---
metric: Payback Period
category: Revenue
difficulty: Intermediate
tags: [SaaS, Subscription, KPI, Unit Economics]
---

# Payback Period — CAC Payback

## Definition

CAC Payback Period is the number of months needed for the gross profit from a new customer (or cohort) to repay the cost of acquiring that customer. It connects CAC, ARPU, and gross margin into a cash-efficiency timeline for growth.

## Formula

```
CAC Payback (months) = CAC / (ARPU × Gross Margin %)
```

Using MRR per customer:

```
Payback = CAC / (Average MRR per new customer × Gross Margin %)
```

Cohort form:

```
Payback = months until cumulative gross profit from cohort ≥ CAC spent to acquire cohort
```

## Business Interpretation

Shorter payback means faster recovery of acquisition cash and more capacity to reinvest in growth. Many SaaS teams aim for payback under ~12 months (sometimes tighter for SMB/PLG, longer acceptable for enterprise with high LTV). Long payback can still work if LTV is high and capital is available — but it increases financing risk. Track payback by channel and segment: paid social might pay back in 4 months while outbound enterprise takes 18.

## Common Mistakes

- Using revenue instead of gross profit in the denominator (understates payback).
- Mixing annual CAC with monthly ARPU without converting units.
- Ignoring that early months may include discounts, free months, or onboarding credits.
- Using blended CAC/ARPU when channel-level payback differs widely.
- Forgetting sales-cycle lag: CAC spent before the customer becomes paying.

## Interview Tips

**Q:** How do you calculate CAC payback, and why do investors care?

**A:** `Payback = CAC / (ARPU × Gross Margin %)`. Investors care because it shows how long growth consumes cash before customers self-fund acquisition. Fast payback supports efficient scaling; long payback needs stronger LTV justification and more capital. Always state margin assumptions and whether CAC is fully loaded.

## SQL Example

```sql
-- Approximate payback by acquisition month cohort
WITH cohort AS (
    SELECT
        DATE_TRUNC('month', first_paid_date) AS cohort_month,
        COUNT(DISTINCT customer_id) AS new_customers,
        AVG(starting_mrr) AS avg_starting_mrr
    FROM customers
    WHERE first_paid_date IS NOT NULL
    GROUP BY 1
),
cac AS (
    SELECT
        DATE_TRUNC('month', spend_date) AS spend_month,
        SUM(amount) AS sm_cost
    FROM sales_marketing_costs
    GROUP BY 1
)
SELECT
    c.cohort_month,
    cac.sm_cost / NULLIF(c.new_customers, 0) AS cac,
    c.avg_starting_mrr,
    (cac.sm_cost / NULLIF(c.new_customers, 0))
        / NULLIF(c.avg_starting_mrr * 0.80, 0) AS payback_months_80pct_margin
FROM cohort c
JOIN cac ON c.cohort_month = cac.spend_month
ORDER BY c.cohort_month;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
