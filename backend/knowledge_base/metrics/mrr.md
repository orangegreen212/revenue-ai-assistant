# MRR — Monthly Recurring Revenue

## Definition

Monthly Recurring Revenue (MRR) is the predictable revenue a subscription business expects to receive every month from active subscriptions. It normalizes all recurring fees to a monthly amount and is the core top-line health metric for SaaS and other subscription models.

## Formula

```
MRR = Σ (monthly subscription fee for each active subscription)
```

For non-monthly billing:

```
MRR from annual plan = Annual contract value / 12
MRR from quarterly plan = Quarterly fee / 3
```

Common components:

```
New MRR       = MRR from newly acquired customers in the period
Expansion MRR = MRR from upgrades, add-ons, or seat increases
Contraction MRR = MRR lost from downgrades
Churned MRR   = MRR lost from cancellations
Net New MRR   = New MRR + Expansion MRR − Contraction MRR − Churned MRR
```

Ending MRR bridge:

```
Ending MRR = Beginning MRR + New MRR + Expansion MRR − Contraction MRR − Churned MRR
```

## Business Interpretation

- **Growth signal:** Rising MRR means the recurring base is expanding; falling MRR signals churn or contraction pressure.
- **Predictability:** Higher share of revenue in MRR usually means more forecastable cash flow than one-time sales.
- **Unit economics link:** Pair MRR with CAC, LTV, and churn to judge whether growth is efficient.
- **Segment view:** Break MRR by plan, cohort, region, or channel to find where growth or risk concentrates.
- **Quality check:** Prefer Net New MRR and retention of existing MRR over growth driven only by aggressive discounting.

## Common Mistakes

1. Including one-time fees (setup, professional services, hardware) in MRR.
2. Counting the full annual invoice as MRR instead of dividing by 12.
3. Mixing recognized revenue (GAAP) with contracted/booked MRR without labeling the difference.
4. Ignoring mid-period upgrades/downgrades or prorations when building the MRR bridge.
5. Treating paused or delinquent subscriptions as fully active MRR without a clear policy.
6. Double-counting seats or add-ons already included in the base subscription.
7. Reporting only Gross New MRR and hiding churn/contraction.

## Interview Tips

- Define MRR clearly before diving into formulas; interviewers often test definitional precision.
- Always distinguish **New / Expansion / Contraction / Churned / Net New MRR**.
- Mention how annual and multi-year deals convert to MRR (divide by 12 / 36, etc.).
- Relate MRR to **ARR** (`ARR = MRR × 12`) and to churn (`Churned MRR / Beginning MRR`).
- Be ready to explain edge cases: trials, freemium, discounts, refunds, and multi-product accounts.
- Show you can build an **MRR bridge** from beginning to ending MRR for a given month.

## SQL Example

```sql
-- Monthly MRR snapshot by customer (normalize all plans to monthly)
WITH subscriptions_normalized AS (
    SELECT
        s.customer_id,
        s.subscription_id,
        s.plan_name,
        s.status,
        s.start_date,
        s.end_date,
        CASE s.billing_interval
            WHEN 'month' THEN s.amount
            WHEN 'quarter' THEN s.amount / 3.0
            WHEN 'year' THEN s.amount / 12.0
            ELSE NULL
        END AS mrr_amount
    FROM subscriptions s
    WHERE s.status = 'active'
)
SELECT
    DATE_TRUNC('month', CURRENT_DATE) AS mrr_month,
    customer_id,
    SUM(mrr_amount) AS customer_mrr
FROM subscriptions_normalized
GROUP BY 1, 2
ORDER BY customer_mrr DESC;
```

MRR bridge sketch:

```sql
-- Illustrative: compare beginning vs ending active MRR in a month
-- (Requires subscription history / event table in a real system)
SELECT
    SUM(CASE WHEN event_type = 'new' THEN mrr_delta ELSE 0 END) AS new_mrr,
    SUM(CASE WHEN event_type = 'expansion' THEN mrr_delta ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN event_type = 'contraction' THEN mrr_delta ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN event_type = 'churn' THEN mrr_delta ELSE 0 END) AS churned_mrr
FROM mrr_events
WHERE event_month = DATE '2026-06-01';
```

## References

- SaaS metrics primers (MRR / ARR / churn frameworks used by operators and investors)
- Internal revenue recognition vs. booked MRR policy (company-specific)
- Subscription billing system docs (Stripe, Chargebee, Recurly, etc.) for proration and status rules
