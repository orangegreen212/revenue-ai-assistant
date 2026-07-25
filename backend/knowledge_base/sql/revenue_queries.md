---
title: Revenue SQL Queries
category: SQL
metric: null
difficulty: Intermediate
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - mrr
  - arr
  - revenue-queries
---

# Definition

This document collects standard SQL query patterns for computing MRR, ARR, and revenue movement (the MRR bridge) from a typical subscriptions table. Table and column names are illustrative — adapt them to your actual schema.

# Why it matters

MRR and ARR are the most frequently recomputed numbers in a SaaS analytics stack, and getting the interval-normalization logic wrong (e.g., failing to convert annual billing to a monthly-equivalent) is one of the most common sources of incorrect dashboards.

# Formula

Assumed schema:

```
subscriptions(
  customer_id, subscription_id, plan_name,
  status, billing_interval, amount,
  start_date, end_date
)
```

# Example

**Current MRR, normalized across billing intervals:**

```sql
SELECT
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year'    THEN amount / 12.0
            ELSE NULL
        END
    ) AS total_mrr
FROM subscriptions
WHERE status = 'active';
```

**Current ARR (annualized):**

```sql
SELECT
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount * 12
            WHEN 'quarter' THEN amount * 4
            WHEN 'year'    THEN amount
            ELSE NULL
        END
    ) AS total_arr
FROM subscriptions
WHERE status = 'active';
```

**MRR by customer:**

```sql
SELECT
    customer_id,
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year'    THEN amount / 12.0
            ELSE NULL
        END
    ) AS customer_mrr
FROM subscriptions
WHERE status = 'active'
GROUP BY customer_id
ORDER BY customer_mrr DESC;
```

**MRR movement bridge between two snapshot dates** (assumes an `mrr_snapshots(customer_id, snapshot_date, mrr)` table):

```sql
WITH beginning AS (
    SELECT customer_id, mrr AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-06-01'
),
ending AS (
    SELECT customer_id, mrr AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-07-01'
)
SELECT
    SUM(CASE WHEN b.customer_id IS NULL THEN e.end_mrr ELSE 0 END) AS new_mrr,
    SUM(CASE WHEN e.end_mrr > b.begin_mrr THEN e.end_mrr - b.begin_mrr ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN e.end_mrr < b.begin_mrr AND e.end_mrr > 0 THEN b.begin_mrr - e.end_mrr ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN e.customer_id IS NULL OR e.end_mrr = 0 THEN b.begin_mrr ELSE 0 END) AS churned_mrr
FROM beginning b
FULL OUTER JOIN ending e ON b.customer_id = e.customer_id;
```

# Common mistakes

- Forgetting to normalize `billing_interval` before summing — mixing monthly and annual amounts directly overstates MRR.
- Filtering only on `status = 'active'` without also checking `end_date`, which can double-count subscriptions that were canceled but not yet marked inactive.
- Using `INNER JOIN` instead of `FULL OUTER JOIN` in the bridge query, which silently drops new or fully-churned customers from the result.

# Related metrics

- **MRR / ARR** — the metrics these queries compute directly.
- **Churn Rate** — see `retention_queries.md` for churn-specific SQL patterns.

# References

- Synthesized standard SQL patterns used across SaaS analytics documentation and billing platform guides (Stripe, Chargebee, Recurly — synthesized, not quoted).

*Note: exact column and table names will differ by schema; these queries are illustrative templates, not tied to a specific production database.*
