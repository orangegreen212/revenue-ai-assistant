---
title: Retention SQL Queries
category: SQL
metric: null
difficulty: Intermediate
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - churn
  - nrr
  - grr
  - retention-queries
---

# Definition

This document collects standard SQL patterns for computing logo churn, revenue churn, and cohort-based NRR/GRR from monthly MRR snapshots.

# Why it matters

Retention metrics are easy to get subtly wrong in SQL — especially the difference between using period-start vs. period-end customer counts as the denominator, and correctly excluding new customers from NRR/GRR.

# Formula

Assumed schema:

```
mrr_snapshots(customer_id, snapshot_date, mrr, status)
```

# Example

**Logo churn and revenue churn for one month:**

```sql
WITH start_customers AS (
    SELECT customer_id, mrr AS start_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-06-01'
      AND status = 'active'
),
churned AS (
    SELECT s.customer_id, s.start_mrr
    FROM start_customers s
    LEFT JOIN mrr_snapshots e
      ON s.customer_id = e.customer_id
     AND e.snapshot_date = DATE '2026-07-01'
    WHERE e.customer_id IS NULL OR e.mrr = 0
)
SELECT
    (SELECT COUNT(*) FROM churned) * 1.0
        / NULLIF((SELECT COUNT(*) FROM start_customers), 0) AS logo_churn_rate,
    (SELECT SUM(start_mrr) FROM churned) * 1.0
        / NULLIF((SELECT SUM(start_mrr) FROM start_customers), 0) AS revenue_churn_rate;
```

**Cohort NRR (net revenue retention) for one period:**

```sql
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-07-01'
    GROUP BY customer_id
)
SELECT
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) AS nrr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
-- Note: new customers acquired after the beginning snapshot are correctly
-- excluded here because the query only iterates over the beginning cohort.
```

**Cohort GRR (expansion excluded, capped at 100%):**

```sql
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-07-01'
    GROUP BY customer_id
)
SELECT
    SUM(LEAST(COALESCE(e.end_mrr, 0), b.begin_mrr)) / NULLIF(SUM(b.begin_mrr), 0) AS grr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
```

# Common mistakes

- Using the ending snapshot's customer list as the base for churn instead of the beginning snapshot — this understates churn.
- Forgetting `LEAST(...)` in the GRR query, which allows expansion to leak in and push GRR above 100%.
- Including customers who joined *after* the beginning snapshot in an NRR/GRR cohort query — the `beginning` CTE must be the sole source of the customer list being joined against.

# Related metrics

- **Churn Rate, NRR, GRR** — the metrics these queries compute directly.
- **Cohort Analysis** — the methodology these queries implement in SQL.

# References

- Synthesized standard SQL patterns used across SaaS analytics documentation (synthesized, not quoted).

*Note: these are illustrative templates; production schemas and edge-case handling (mid-period plan changes, proration) will require adaptation.*
