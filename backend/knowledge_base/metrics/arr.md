---
title: Annual Recurring Revenue
category: Metrics
metric: ARR
difficulty: Beginner
source:
  - Stripe Documentation (synthesized)
  - Industry-standard SaaS metric definitions
tags:
  - saas
  - revenue
  - recurring revenue
  - board-reporting
---

# Definition

Annual Recurring Revenue (ARR) is the annualized value of a subscription business's recurring revenue base. It is the standard metric used for board reporting, fundraising, and year-over-year growth comparisons because it removes monthly noise and expresses recurring revenue on a yearly scale.

# Why it matters

ARR is the headline number investors, boards, and executives use to gauge company scale and trajectory. Because it is derived directly from MRR, ARR should never be treated as a separate, independently-measured figure — any inconsistency between how MRR and ARR are calculated will produce contradictory reporting.

# Formula

```
ARR = MRR × 12
```

Direct annualization from contracts:

```
ARR = Σ (annualized recurring fee for each active subscription)
```

ARR movement bridge (mirrors the MRR bridge, annualized):

```
Ending ARR = Beginning ARR + New ARR + Expansion ARR
             − Contraction ARR − Churned ARR
```

# Example

```
Current MRR = $6,000
ARR = $6,000 × 12 = $72,000
```

For a multi-year contract worth $180,000 over 3 years:

```
ARR contribution = $180,000 / 3 = $60,000 per year
```

This annualized figure is what should appear in ARR reporting — not the full $180,000 booked in year one.

# Common mistakes

- Booking the full value of a multi-year contract as ARR in the first year instead of annualizing it.
- Including one-time implementation or professional-services fees in ARR.
- Reporting "booked ARR" (signed but not yet live) as if it were active, revenue-generating ARR.
- Using a different rounding or proration method for ARR than the one used for MRR, causing `ARR ≠ MRR × 12` in internal reports.
- Treating ARR growth as automatically healthy without checking whether it is being driven by discounting or one-time promotional pricing.

# Related metrics

- **MRR** — the monthly figure ARR is derived from.
- **NRR** — shows how ARR from an existing cohort evolves after expansion and churn, independent of new-logo growth.
- **CAC Payback** — often expressed against ARR or MRR contribution per customer to gauge how quickly acquisition cost is recovered.

# References

- Stripe Billing documentation (recurring billing concepts, synthesized)
- Common SaaS metrics frameworks used industry-wide (synthesized, not quoted)

*Note: what counts as "good" ARR growth varies enormously by stage (seed vs. growth vs. late-stage) and is not stated here as a fixed number.*
