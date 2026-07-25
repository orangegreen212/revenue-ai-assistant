---
title: Subscription SQL Queries
category: SQL
metric: null
difficulty: Beginner
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - subscriptions
  - arpu
  - cac
  - subscription-queries
---

# Definition

This document collects SQL patterns for subscription-level analysis: ARPU by plan, active subscription counts, and blended CAC.

# Why it matters

These are the queries most commonly used to feed pricing decisions, plan-mix analysis, and acquisition-efficiency reviews — they translate raw subscription and cost data into the per-customer/per-plan metrics leadership actually reviews.

# Formula

Assumed schema (in addition to `subscriptions`):

```
customers(customer_id, first_paid_date)
sales_marketing_costs(spend_date, amount)
```

# Example

**ARPU by plan:**

```sql
SELECT
    plan_name,
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year'    THEN amount / 12.0
            ELSE NULL
        END
    ) / NULLIF(COUNT(DISTINCT customer_id), 0) AS arpu
FROM subscriptions
WHERE status = 'active'
GROUP BY plan_name
ORDER BY arpu DESC;
```

**Active subscription count by plan:**

```sql
SELECT
    plan_name,
    COUNT(*) AS active_subscriptions
FROM subscriptions
WHERE status = 'active'
GROUP BY plan_name
ORDER BY active_subscriptions DESC;
```

**Blended CAC by month:**

```sql
WITH new_customers AS (
    SELECT
        DATE_TRUNC('month', first_paid_date) AS cohort_month,
        COUNT(DISTINCT customer_id) AS new_customer_count
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
    n.new_customer_count,
    s.sm_cost / NULLIF(n.new_customer_count, 0) AS cac
FROM new_customers n
JOIN sm_spend s ON n.cohort_month = s.spend_month
ORDER BY n.cohort_month;
```

# Common mistakes

- Computing ARPU with `COUNT(*)` instead of `COUNT(DISTINCT customer_id)`, which overcounts customers with multiple active subscriptions.
- Joining new-customer counts to spend by calendar month without accounting for the lag between spend and conversion — a more accurate model attributes spend to the cohort it actually influenced.
- Mixing paid and organic acquisition into "blended CAC" when the question actually requires channel-level CAC.

# Related metrics

- **ARPU, CAC** — the metrics these queries compute directly.
- **Customer Segmentation** — plan-level breakdowns are a basic form of segmentation.

# References

- Synthesized standard SQL patterns used across SaaS analytics documentation (synthesized, not quoted).

*Note: illustrative templates; adapt table/column names and attribution logic to your actual billing and marketing-cost schema.*
