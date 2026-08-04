---
title: Customer Lifetime Value
category: Metrics
metric: LTV
difficulty: Intermediate
source:
  - ProfitWell Resources (synthesized)
  - Reforge (synthesized)
tags:
  - saas
  - unit-economics
  - retention
  - forecasting
---

# Definition

Customer Lifetime Value (LTV, also written CLV) estimates the total gross profit a business expects to earn from a customer over the entire duration of their relationship with the company. In SaaS, LTV is typically derived from ARPU, gross margin, and churn rate rather than tracked customer-by-customer.

# Why it matters

LTV is the counterweight to CAC — together they define whether a company's growth engine is economically sustainable. LTV also indicates how much a business can afford to invest in acquisition, retention programs, or customer success without destroying unit economics.

# Formula

**Standard SaaS formula (gross-profit based):**

LTV = ARPU × Gross Margin % / Customer Churn Rate

**Equivalent lifetime-based form:**

Average Customer Lifetime (months) = 1 / Monthly Churn Rate
LTV = ARPU × Gross Margin % × Average Customer Lifetime

Using **revenue** instead of gross profit produces "Revenue LTV," which overstates true customer value and should not be used in LTV:CAC ratios.

# Example

A customer pays $100/month (ARPU), the business has 80% gross margin, and monthly churn is 2%.

Average lifetime = 1 / 0.02 = 50 months
LTV = $100 × 0.80 × 50 = $4,000

# Common mistakes

- Using revenue instead of gross profit in the LTV:CAC ratio, which inflates the ratio and hides a potentially unsustainable economics.
- Mixing monthly ARPU with an annual churn rate (or vice versa) without converting units consistently.
- Assuming a flat, constant churn rate when early cohorts often churn faster than mature ones — a cohort-based LTV is more accurate than a single blended estimate.
- Ignoring expansion revenue, which understates LTV for accounts that grow over time.
- Applying one blended LTV figure across very different customer segments or acquisition channels when making pricing or channel-investment decisions.

# Related metrics

- **CAC** — LTV is only actionable when compared against CAC via the LTV:CAC ratio.
- **Churn Rate** — the primary driver of the "lifetime" component of LTV.
- **ARPU** — the revenue-per-account input to the LTV formula.
- **Gross Margin** — converts revenue-based ARPU into profit-based LTV.

# References

- ProfitWell SaaS metrics resources (synthesized, not quoted)
- Reforge growth and retention essays (synthesized, not quoted)

*Note: commonly cited "healthy" LTV:CAC ratios (such as 3:1) are rules of thumb repeated across the industry, not universal laws — actual targets vary by capital efficiency goals, growth stage, and market. No single number is asserted as correct here.*
