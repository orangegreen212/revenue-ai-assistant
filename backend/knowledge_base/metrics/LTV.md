---
metric: LTV
category: Revenue
difficulty: Intermediate
tags: [SaaS, Subscription, KPI, Unit Economics]
---

# LTV — Customer Lifetime Value

## Definition

Customer Lifetime Value (LTV, or CLV) estimates the total gross profit (or sometimes revenue) expected from a customer over the entire relationship. In SaaS, LTV is usually derived from ARPU, gross margin, and churn (or lifetime in months). It is used with CAC to judge whether acquisition is economically sustainable.

## Formula

Simple gross-margin LTV (classic SaaS):

```
LTV = ARPU × Gross Margin % / Customer Churn Rate
```

Using lifetime in months:

```
Average customer lifetime (months) = 1 / Monthly churn rate
LTV = ARPU × Gross Margin % × Average customer lifetime
```

Revenue-only variant (less preferred for unit economics):

```
LTV_revenue = ARPU / Churn Rate
```

Cohort LTV (more accurate):

```
LTV = Σ (discounted expected gross profit by month for the cohort)
```

## Business Interpretation

LTV answers how much value a customer creates over time. Healthy SaaS often targets **LTV:CAC ≥ 3:1**, with CAC payback under ~12 months (context-dependent). If LTV is calculated on revenue instead of gross profit, ratios look artificially strong. Segment LTV by plan and acquisition channel — a high blended LTV can hide that one channel acquires low-retention customers. Improving LTV usually comes from lower churn, higher ARPU/expansion, or better gross margin.

## Common Mistakes

- Using revenue LTV in an LTV:CAC ratio instead of gross-profit LTV.
- Applying annual churn in a monthly ARPU formula (units must match).
- Assuming constant churn when early cohorts churn much faster than later ones.
- Ignoring expansion (understates LTV) or counting it twice.
- Using a single blended LTV for pricing and channel decisions across segments.

## Interview Tips

**Q:** How do you calculate LTV, and what LTV:CAC ratio is considered healthy?

**A:** A common formula is `LTV = ARPU × Gross Margin % / Churn`. Match periods (monthly ARPU with monthly churn). Prefer gross-profit LTV for CAC comparisons. A rule of thumb is LTV:CAC around 3:1 or higher, but also check payback period and cash constraints. Mention cohort-based LTV as more accurate when churn and expansion vary over time.

## SQL Example

```sql
-- Approximate LTV by plan using monthly ARPU, margin, and monthly logo churn
WITH plan_arpu AS (
    SELECT
        plan_name,
        AVG(mrr) AS arpu
    FROM subscriptions
    WHERE status = 'active'
    GROUP BY plan_name
),
plan_churn AS (
    SELECT
        plan_name,
        COUNT(*) FILTER (WHERE churned_in_month) * 1.0
            / NULLIF(COUNT(*) FILTER (WHERE active_at_month_start), 0) AS monthly_churn
    FROM subscription_month_facts
    GROUP BY plan_name
)
SELECT
    a.plan_name,
    a.arpu,
    c.monthly_churn,
    (a.arpu * 0.80) / NULLIF(c.monthly_churn, 0) AS ltv_gross_profit_80pct_margin
FROM plan_arpu a
JOIN plan_churn c ON a.plan_name = c.plan_name;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
