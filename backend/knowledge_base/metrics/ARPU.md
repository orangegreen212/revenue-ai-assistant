---
metric: ARPU
category: Revenue
difficulty: Beginner
tags: [SaaS, Subscription, KPI]
---

# ARPU — Average Revenue Per User

## Definition

Average Revenue Per User (ARPU) is the average recurring revenue generated per customer (or per active account/user) in a period. In B2B SaaS it is often calculated per account rather than per seat; clarify whether you mean per customer, per seat, or per MAU.

## Formula

```
ARPU = Total MRR (or recurring revenue) / Number of active customers
```

Per-seat variant:

```
ARPU_seat = Total MRR / Number of active paid seats
```

Period variants:

```
Monthly ARPU = MRR / Active customers
Annual ARPU  = ARR / Active customers
```

## Business Interpretation

ARPU shows monetization intensity of the customer base. Rising ARPU usually comes from price increases, plan mix shift, expansion, or moving upmarket. Falling ARPU can signal discounting, downsells, or a mix shift toward lower-priced SMB. Pair ARPU with customer count growth: revenue can grow from more logos, higher ARPU, or both (a simple bridge). For product-led SaaS, also track ARPU alongside conversion from free to paid.

## Common Mistakes

- Mixing users, seats, and accounts in the denominator without defining “user.”
- Including one-time fees in the numerator while calling it subscription ARPU.
- Comparing ARPU across companies with different packaging (per-seat vs flat subscription).
- Using end-of-month actives when revenue was earned by a different activity base mid-month.
- Ignoring currency and discounting effects when analyzing ARPU trends.

## Interview Tips

**Q:** Revenue grew 20% while customers grew 5% — what does that imply for ARPU?

**A:** Roughly, ARPU increased: growth came more from monetization (price, mix, expansion) than from logo growth. A clean answer decomposes revenue growth into customer growth × ARPU growth (plus interaction effects) and then checks whether ARPU rose from expansion, pricing, or mix shift toward larger accounts.

## SQL Example

```sql
-- Monthly ARPU by plan
SELECT
    snapshot_date,
    plan_name,
    SUM(mrr) AS total_mrr,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(mrr) / NULLIF(COUNT(DISTINCT customer_id), 0) AS arpu
FROM mrr_snapshots
WHERE status = 'active'
GROUP BY snapshot_date, plan_name
ORDER BY snapshot_date, plan_name;
```

## References

- Stripe Billing Documentation
- Paddle SaaS Metrics Guide
