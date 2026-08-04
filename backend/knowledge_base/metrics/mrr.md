---
title: Monthly Recurring Revenue
category: Metrics
metric: MRR
difficulty: Beginner
source:
  - Stripe Documentation (synthesized)
  - Industry-standard SaaS metric definitions
tags:
  - saas
  - revenue
  - recurring revenue
  - top-line
---

# Definition

Monthly Recurring Revenue (MRR) is the predictable, normalized revenue a subscription business expects to receive every month from active subscriptions. All billing intervals (monthly, quarterly, annual) are converted to a monthly-equivalent figure so revenue can be compared and tracked consistently period over period.

# Why it matters

MRR is the primary top-line health metric for subscription businesses. It removes the noise of one-time payments, discounts, and irregular billing cycles, leaving a clean signal of how the recurring revenue base is trending. Finance, sales, and product teams all use MRR as a shared reference point for growth, forecasting, and board reporting.

# Formula

MRR = Σ (monthly-equivalent recurring fee for each active subscription)

Normalizing non-monthly billing:

MRR from an annual plan    = Annual Contract Value / 12
MRR from a quarterly plan  = Quarterly fee / 3

MRR movement bridge (used to explain a change between two months):

Ending MRR = Beginning MRR + New MRR + Expansion MRR
             − Contraction MRR − Churned MRR

| Component | Meaning |
|---|---|
| New MRR | MRR from customers acquired during the period |
| Expansion MRR | Additional MRR from upgrades, add-ons, or seat growth |
| Contraction MRR | MRR lost from downgrades (customer still active) |
| Churned MRR | MRR lost from full cancellations |

# Example

A company has 100 customers on a $50/month plan and 20 customers on a $600/year plan.

Monthly plan MRR   = 100 × $50           = $5,000
Annual plan MRR    = 20 × ($600 / 12)    = $1,000
Total MRR                                = $6,000

# Common mistakes

- Including one-time fees (setup, professional services, hardware) in MRR.
- Treating a full annual invoice as MRR instead of dividing by 12.
- Mixing recognized (GAAP) revenue with contracted/booked MRR without labeling which one is being reported.
- Ignoring mid-month proration when a customer upgrades, downgrades, or cancels partway through a billing cycle.
- Counting paused, trialing, or past-due subscriptions as fully active MRR without a documented policy for how each status is treated.

# Related metrics

- **ARR** — MRR annualized (`ARR = MRR × 12`); used for board-level and annual reporting.
- **Churn Rate** — the rate at which MRR (or customers) is lost; a direct input to the MRR bridge.
- **NRR / GRR** — cohort-based retention views that explain *why* MRR moved for a specific group of customers.
- **ARPU** — MRR divided by active customer count; shows monetization intensity per account.

# References

- Stripe Billing documentation (subscription and invoicing concepts, synthesized)
- Common SaaS metrics frameworks used across the industry (ChartMogul, ProfitWell, Baremetrics glossaries — synthesized, not quoted)

*Note: exact benchmark ranges for "healthy" MRR growth vary significantly by company stage, industry, and go-to-market motion — no single universal target is cited here.*
