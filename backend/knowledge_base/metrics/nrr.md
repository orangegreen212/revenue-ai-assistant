---
title: Net Revenue Retention
category: Metrics
metric: NRR
difficulty: Intermediate
source:
  - Bessemer Cloud Index (synthesized)
  - OpenView SaaS Benchmarks (synthesized)
  - Winning by Design (synthesized)
tags:
  - saas
  - retention
  - expansion
  - cohort
---

# Definition

Net Revenue Retention (NRR), also called Net Dollar Retention (NDR), measures how much recurring revenue from a **specific starting cohort** of customers changes over a period, after accounting for expansion (upsells, seat growth), contraction (downgrades), and churn. New customers acquired during the period are explicitly excluded — NRR only tracks what happens to revenue that already existed at the start of the window.

# Why it matters

NRR is one of the strongest signals of product-market fit and account health available to a SaaS company. An NRR above 100% means the existing customer base is growing on its own — through upgrades and expansion — even before counting any new-logo acquisition. This is often called "negative churn" and is treated as a hallmark of a strong retention motion by investors and operators alike.

# Formula

**Revenue bridge method:**

```
NRR = (Beginning ARR + Expansion − Contraction − Churn) / Beginning ARR
```

**Cohort method (equivalent):**

```
NRR = Ending ARR of starting cohort / Beginning ARR of starting cohort
```

Unlike GRR, NRR has no upper cap — it can exceed 100%.

# Example

A cohort starts the year with $1,000,000 ARR. Over the year: $150,000 of expansion, $40,000 of contraction, and $60,000 of churn.

```
NRR = ($1,000,000 + $150,000 − $40,000 − $60,000) / $1,000,000
NRR = $1,050,000 / $1,000,000 = 105%
```

# Common mistakes

- Including new customers acquired during the period in the NRR calculation — this belongs to New ARR / logo growth, not NRR.
- Mixing recognized revenue with contracted ARR when defining "beginning" and "ending" values for the cohort.
- Reporting a single blended NRR number while a small number of large expansions mask widespread churn in the rest of the base (segment-level NRR often tells a very different story than the blended figure).
- Comparing NRR across companies without confirming they use the same measurement window (monthly vs. trailing-twelve-month NRR are not directly comparable).

# Related metrics

- **GRR** — the retention-only counterpart to NRR; excludes expansion and is capped at 100%. `NRR = GRR + (Expansion / Beginning ARR)`.
- **Churn Rate** — one of the components subtracted in the NRR bridge.
- **ARR** — the base unit NRR is measured against.
- **Customer Segmentation** — NRR should be reviewed by segment (plan tier, company size, cohort age), not only as a single blended figure.

# References

- Bessemer Cloud Index (public benchmark commentary on retention metrics, synthesized)
- OpenView SaaS Benchmarks reports (synthesized, not quoted)
- Winning by Design revenue architecture materials (synthesized, not quoted)

*Note: "good" NRR benchmarks vary by company stage, segment (SMB vs. enterprise), and industry. Publicly cited ranges differ across sources and years, so no single fixed number is asserted here — consult current benchmark reports for up-to-date figures.*
