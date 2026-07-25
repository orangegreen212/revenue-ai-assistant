---
title: Cohort SQL Queries
category: SQL
metric: null
difficulty: Advanced
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - cohort-analysis
  - retention
  - cohort-queries
---

# Definition

This document collects SQL patterns for building cohort retention tables — grouping customers by signup month and tracking their retention over subsequent months, the SQL implementation of the Cohort Analysis framework.

# Why it matters

Cohort tables are one of the more complex standard queries in SaaS analytics because they require generating a full grid of (cohort_month × observation_month) combinations, not just a single aggregation — a naive `GROUP BY` alone cannot produce this shape.

# Formula

Assumed schema:

```
customers(customer_id, signup_date)
mrr_snapshots(customer_id, snapshot_date, mrr, status)
```

# Example

**Cohort logo-retention table (% of each cohort still active N months after signup):**

```sql
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT
        m.customer_id,
        c.cohort_month,
        DATE_TRUNC('month', m.snapshot_date) AS activity_month,
        (DATE_PART('year', m.snapshot_date) - DATE_PART('year', c.cohort_month)) * 12
            + (DATE_PART('month', m.snapshot_date) - DATE_PART('month', c.cohort_month)) AS months_since_signup
    FROM mrr_snapshots m
    JOIN cohorts c ON m.customer_id = c.customer_id
    WHERE m.status = 'active'
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.months_since_signup,
    COUNT(DISTINCT a.customer_id) AS active_customers,
    cs.cohort_size,
    COUNT(DISTINCT a.customer_id) * 1.0 / NULLIF(cs.cohort_size, 0) AS retention_rate
FROM activity a
JOIN cohort_sizes cs ON a.cohort_month = cs.cohort_month
GROUP BY a.cohort_month, a.months_since_signup, cs.cohort_size
ORDER BY a.cohort_month, a.months_since_signup;
```

**Cohort revenue retention (NRR-style, per cohort per month since signup):**

```sql
WITH cohorts AS (
    SELECT customer_id, DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
cohort_start_mrr AS (
    SELECT c.cohort_month, SUM(m.mrr) AS starting_mrr
    FROM mrr_snapshots m
    JOIN cohorts c ON m.customer_id = c.customer_id
    WHERE DATE_TRUNC('month', m.snapshot_date) = c.cohort_month
    GROUP BY c.cohort_month
),
cohort_mrr_by_month AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC('month', m.snapshot_date) AS activity_month,
        SUM(m.mrr) AS mrr_that_month
    FROM mrr_snapshots m
    JOIN cohorts c ON m.customer_id = c.customer_id
    GROUP BY c.cohort_month, DATE_TRUNC('month', m.snapshot_date)
)
SELECT
    cb.cohort_month,
    cb.activity_month,
    cb.mrr_that_month,
    cs.starting_mrr,
    cb.mrr_that_month / NULLIF(cs.starting_mrr, 0) AS cohort_nrr
FROM cohort_mrr_by_month cb
JOIN cohort_start_mrr cs ON cb.cohort_month = cs.cohort_month
ORDER BY cb.cohort_month, cb.activity_month;
```

# Common mistakes

- Computing `months_since_signup` with naive date subtraction instead of proper year/month arithmetic, causing off-by-one errors around year boundaries.
- Using cohort size measured *today* instead of the size at the cohort's starting month, which distorts retention percentages for older cohorts.
- Forgetting that cohort tables can be very expensive to compute on large datasets — pre-aggregating into a monthly snapshot table (rather than computing from raw event data every time) is standard practice.

# Related metrics

- **Cohort Analysis** — the conceptual framework these queries implement.
- **NRR / GRR / Churn Rate** — the metrics cohort tables are typically built to visualize over time.

# References

- Synthesized standard SQL patterns used across SaaS analytics documentation (synthesized, not quoted).

*Note: illustrative templates using ANSI SQL date functions; exact syntax (DATE_TRUNC, DATE_PART, etc.) varies by database engine (Postgres, Snowflake, BigQuery).*
