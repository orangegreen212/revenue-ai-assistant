---
title: Gross Revenue Retention
category: Metrics
metric: GRR
difficulty: Intermediate
source:
  - Bessemer Cloud Index (synthesized)
  - OpenView SaaS Benchmarks (synthesized)
tags:
  - saas
  - retention
  - churn
  - cohort
---

# Definition

Gross Revenue Retention (GRR), also called Gross Dollar Retention (GDR), measures how much recurring revenue from a starting cohort is retained after churn and contraction — **excluding any expansion revenue**. It isolates the quality of retention on its own, without upsells masking underlying churn.

# Why it matters

GRR answers a narrower, stricter question than NRR: "Are we keeping the revenue we already had?" Because expansion is excluded, GRR can never exceed 100%. This makes it a cleaner diagnostic for churn and downgrade problems — a company can have strong NRR from a few large expansions while GRR reveals that churn across the broader base is a real problem.

# Formula

```
GRR = (Beginning ARR − Contraction − Churn) / Beginning ARR
```

Relationship to NRR:

```
NRR = GRR + (Expansion / Beginning ARR)
```

GRR is mathematically capped at 100% — reporting GRR above 100% indicates expansion was mistakenly included.

# Example

Same cohort as the NRR example: $1,000,000 beginning ARR, $40,000 contraction, $60,000 churn (expansion is excluded here).

```
GRR = ($1,000,000 − $40,000 − $60,000) / $1,000,000
GRR = $900,000 / $1,000,000 = 90%
```

# Common mistakes

- Accidentally including expansion revenue, which allows GRR to appear above 100% — a value that is not mathematically valid for this metric.
- Using different cohort windows for GRR and NRR (e.g., monthly GRR vs. annual NRR) and then comparing them directly.
- Treating a high blended GRR as sufficient evidence of health without checking whether one large segment (e.g., enterprise) is propping up a much weaker SMB segment.
- Confusing GRR (revenue-based) with logo/customer retention (count-based) — a company can retain most of its revenue while still losing many small accounts.

# Related metrics

- **NRR** — adds expansion back in; `NRR = GRR + (Expansion / Beginning ARR)`.
- **Churn Rate** — GRR is essentially 100% minus the revenue-churn and contraction rates combined.
- **Customer Segmentation** — GRR should be broken out by plan, segment, and cohort age to find where retention problems concentrate.

# References

- Bessemer Cloud Index (public benchmark commentary, synthesized)
- OpenView SaaS Benchmarks reports (synthesized, not quoted)

*Note: "healthy" GRR ranges are frequently cited in industry benchmark reports but vary by segment and company stage — no fixed number is stated here; refer to current benchmark sources for figures relevant to a specific segment.*
