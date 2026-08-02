"""Illustrative SQL-snippet generator for common SaaS revenue metrics."""

from langchain_core.tools import tool

@tool
def generate_sql(metric_or_question: str, table_hint: str = "subscriptions") -> str:
    """Generate a simple illustrative SQL snippet for a SaaS metric or analytics question.

    Args:
        metric_or_question: Metric name (e.g. MRR, churn) or a short question.
        table_hint: Primary table name to use in the SQL (default: subscriptions).
    """
    q = metric_or_question.strip().lower()
    table = table_hint.strip() or "subscriptions"

    if "nrr" in q or "net revenue retention" in q or "net dollar" in q:
        return f"""-- Net Revenue Retention (illustrative cohort SQL)
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
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) AS nrr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;"""

    if "grr" in q or "gross revenue retention" in q or "gross dollar" in q:
        return f"""-- Gross Revenue Retention (expansion excluded / capped)
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
        / NULLIF(SUM(b.begin_mrr), 0) AS grr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;"""

    if "churn" in q:
        return f"""-- Logo and revenue churn for one month
WITH start_customers AS (
    SELECT customer_id, mrr AS start_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
),
churned AS (
    SELECT s.customer_id, s.start_mrr
    FROM start_customers s
    LEFT JOIN mrr_snapshots e
      ON s.customer_id = e.customer_id
     AND e.snapshot_date = DATE '2026-02-01'
    WHERE e.customer_id IS NULL OR e.mrr = 0
)
SELECT
    (SELECT COUNT(*) FROM churned) * 1.0
        / NULLIF((SELECT COUNT(*) FROM start_customers), 0) AS logo_churn_rate,
    (SELECT SUM(start_mrr) FROM churned) * 1.0
        / NULLIF((SELECT SUM(start_mrr) FROM start_customers), 0) AS revenue_churn_rate;"""

    if "cac" in q or "acquisition" in q:
        return f"""-- Blended CAC by month
SELECT
    DATE_TRUNC('month', c.first_paid_date) AS cohort_month,
    SUM(s.amount) / NULLIF(COUNT(DISTINCT c.customer_id), 0) AS cac
FROM customers c
JOIN sales_marketing_costs s
  ON DATE_TRUNC('month', s.spend_date) = DATE_TRUNC('month', c.first_paid_date)
GROUP BY 1
ORDER BY 1;"""

    if "ltv" in q or "lifetime" in q:
        return f"""-- Approximate LTV by plan (ARPU * margin / monthly churn)
SELECT
    plan_name,
    AVG(mrr) AS arpu,
    (AVG(mrr) * 0.80) / NULLIF(AVG(monthly_churn_rate), 0) AS ltv_est
FROM {table}
GROUP BY plan_name;"""

    if "arpu" in q:
        return f"""-- ARPU by plan
SELECT
    plan_name,
    SUM(mrr) / NULLIF(COUNT(DISTINCT customer_id), 0) AS arpu
FROM {table}
WHERE status = 'active'
GROUP BY plan_name;"""

    if "arr" in q:
        return f"""-- ARR snapshot from active subscriptions
SELECT
    SUM(
        CASE billing_interval
            WHEN 'month' THEN amount * 12
            WHEN 'quarter' THEN amount * 4
            WHEN 'year' THEN amount
            ELSE NULL
        END
    ) AS total_arr
FROM {table}
WHERE status = 'active';"""

    if "payback" in q:
        return f"""-- CAC payback months by cohort (assumes 80% gross margin)
SELECT
    cohort_month,
    cac / NULLIF(avg_starting_mrr * 0.80, 0) AS payback_months
FROM cohort_unit_economics
ORDER BY cohort_month;"""

    # Default: MRR-style query
    return f"""-- MRR by customer (normalize billing intervals to monthly)
SELECT
    customer_id,
    SUM(
        CASE billing_interval
            WHEN 'month' THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year' THEN amount / 12.0
            ELSE NULL
        END
    ) AS customer_mrr
FROM {table}
WHERE status = 'active'
GROUP BY customer_id
ORDER BY customer_mrr DESC;
-- Tip: rephrase with a metric name (MRR, ARR, NRR, churn, CAC, LTV, ARPU, payback)
-- for a more targeted template. Question was: {metric_or_question}"""
