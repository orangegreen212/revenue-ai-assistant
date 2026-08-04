---
metric: Sales Funnel
category: Revenue
difficulty: Beginner
tags: [SaaS, Subscription, KPI, Growth]
---

# Sales Funnel — SaaS Conversion Metrics

## Definition

The Sales Funnel is the staged path from awareness to paying customer (and often to expansion). In SaaS it typically includes marketing and sales stages such as visitor → lead → MQL → SQL → opportunity → closed-won, or a product-led path such as visit → signup → activation → conversion to paid. Funnel analytics measure volume, conversion rates, and velocity between stages.

## Formula

Stage conversion rate:

Conversion (A → B) = Count reaching stage B / Count entering stage A

Overall funnel conversion:

Visitor-to-paid = Paid customers / Visitors

Funnel throughput (example):


Expected wins = Opportunities × Win rate
Pipeline coverage = Pipeline value / Revenue target

Sales velocity (simplified):

Velocity ≈ (# opportunities × win rate × avg deal size) / sales cycle length

## Business Interpretation

The funnel shows where growth leaks. A strong top-of-funnel with weak SQL-to-win rates points to sales or ICP problems; strong win rates with few MQLs point to demand gen. For PLG, activation and time-to-value often matter more than classic MQL counts. Review both **rates** and **absolute volumes**, and segment the funnel by channel, segment, and product. Tie funnel output to CAC, payback, and new MRR so marketing/sales KPIs stay connected to revenue.

## Common Mistakes

- Comparing conversion rates across stages with inconsistent stage definitions in the CRM.
- Optimizing vanity top-of-funnel volume that never becomes pipeline.
- Ignoring time lags (this month’s MQLs become next quarter’s revenue).
- Mixing self-serve and enterprise motions in one funnel without separate paths.
- Tracking stage counts without win rate, cycle time, and average deal size.

## Interview Tips

**Q:** How would you diagnose a drop in new MRR using the sales funnel?

**A:** Build a bridge from new MRR back through closed-won → opportunities → SQLs → MQLs → leads, by channel and segment. Check whether volume fell, conversion rates fell, deal size fell, or cycle time stretched. Example: MQLs flat but win rate down may be ICP or competitive pressure; win rate flat but MQLs down is demand generation. Quantify the largest gap and propose one experiment per bottleneck.

## SQL Example

sql
-- Funnel conversion by month (CRM-style stages)
WITH stages AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        COUNT(*) FILTER (WHERE stage_reached >= 'lead') AS leads,
        COUNT(*) FILTER (WHERE stage_reached >= 'mql') AS mqls,
        COUNT(*) FILTER (WHERE stage_reached >= 'sql') AS sqls,
        COUNT(*) FILTER (WHERE stage_reached >= 'opportunity') AS opportunities,
        COUNT(*) FILTER (WHERE stage_reached >= 'closed_won') AS wins
    FROM funnel_events
    GROUP BY 1
)
SELECT
    month,
    leads,
    mqls,
    sqls,
    opportunities,
    wins,
    mqls * 1.0 / NULLIF(leads, 0) AS lead_to_mql,
    sqls * 1.0 / NULLIF(mqls, 0) AS mql_to_sql,
    wins * 1.0 / NULLIF(opportunities, 0) AS opportunity_win_rate
FROM stages
ORDER BY month;


## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
