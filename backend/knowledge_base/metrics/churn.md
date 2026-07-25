---
title: Churn Rate
category: Metrics
metric: Churn
difficulty: Beginner
source:
  - ProfitWell Resources (synthesized)
  - HubSpot Knowledge Base (synthesized)
tags:
  - saas
  - retention
  - churn
  - risk
---

# Definition

Churn Rate measures the pace at which customers or recurring revenue are lost over a period. **Logo churn** (also called customer churn) counts lost accounts; **revenue churn** measures lost MRR/ARR from cancellations (and sometimes downgrades, depending on definition). Both are central risk indicators for subscription businesses.

# Why it matters

Churn directly limits how large a recurring revenue base can grow, no matter how strong new-customer acquisition is. A business adding customers quickly but losing them just as quickly ("leaky bucket") will struggle to compound growth. Churn also feeds directly into LTV — lower churn means a longer average customer lifetime and a higher LTV.

# Formula

**Logo churn rate:**

```
Logo Churn Rate = Customers Lost in Period / Customers at Start of Period
```

**Revenue churn rate:**

```
Revenue Churn Rate = MRR Lost in Period / MRR at Start of Period
```

**Gross vs. net revenue churn:**

```
Gross Revenue Churn = (Churned MRR + Contraction MRR) / Beginning MRR
Net Revenue Churn   = (Churned MRR + Contraction MRR − Expansion MRR) / Beginning MRR
```

Approximate average customer lifetime from monthly churn:

```
Average Lifetime (months) ≈ 1 / Monthly Logo Churn Rate
```

# Example

A company starts the month with 500 customers and 20 cancel.

```
Logo Churn Rate = 20 / 500 = 4%
```

If those 20 customers represented $3,000 of a $60,000 starting MRR:

```
Revenue Churn Rate = $3,000 / $60,000 = 5%
```

# Common mistakes

- Blending logo churn and revenue churn into a single "churn number" without labeling which one is being reported — they answer different questions and can diverge significantly.
- Using the customer count at period-**end** as the denominator instead of the count at period-**start**.
- Annualizing monthly churn by simply multiplying by 12, which overstates the true annual figure (the correct compounding formula is `1 − (1 − monthly churn)^12`).
- Counting downgrades as full churn, or ignoring them entirely, instead of tracking them separately as contraction.
- Failing to separate voluntary churn (customer chooses to cancel) from involuntary churn (failed payment), since the fixes for each are completely different (product/CS work vs. payment-retry/dunning logic).

# Related metrics

- **GRR / NRR** — retention metrics that are the inverse framing of churn at the cohort level.
- **LTV** — churn rate is a direct driver of average customer lifetime and therefore LTV.
- **Customer Segmentation** — churn should be reviewed by cohort, plan, and tenure, since early-lifecycle churn often dominates blended figures.

# References

- ProfitWell SaaS metrics resources (synthesized, not quoted)
- HubSpot SaaS metrics knowledge base (synthesized, not quoted)

*Note: "acceptable" churn ranges differ enormously between SMB and enterprise SaaS, and between monthly and annual contracts — no fixed benchmark number is asserted here.*
