---
title: Cohort Analysis
category: Frameworks
metric: null
difficulty: Intermediate
source:
  - ProfitWell Resources (synthesized)
  - Reforge (synthesized)
tags:
  - cohort-analysis
  - retention
  - saas
  - methodology
---

# Definition

Cohort analysis groups customers by a shared starting characteristic — most commonly the month they signed up — and tracks how that specific group's behavior (retention, revenue, expansion) evolves over time. This isolates trends by tenure rather than mixing customers of very different ages into one blended snapshot.

# Why it matters

A single point-in-time churn or NRR number can be misleading because it blends customers who joined last month with customers who joined three years ago — and early-lifecycle behavior is usually very different from mature-account behavior. Cohort analysis is the standard method for answering "is our product actually getting stickier over time?" — a question a blended snapshot cannot answer on its own.

# Formula

Cohort retention at month N:

Cohort Retention (Month N) = Customers from Cohort still active at Month N / Customers in Cohort at Month 0

Cohort revenue retention (the basis for NRR/GRR when applied to one specific cohort):

Cohort NRR (Month N) = Cohort ARR at Month N / Cohort ARR at Month 0

Cohorts are typically laid out in a triangular retention table:

| Cohort | Month 0 | Month 1 | Month 2 | Month 3 |
|---|---|---|---|---|
| Jan cohort | 100% | 92% | 88% | 85% |
| Feb cohort | 100% | 90% | 84% | — |
| Mar cohort | 100% | 94% | — | — |

# Example

The January signup cohort starts with 200 customers. Three months later, 170 are still active.

Month-3 Retention = 170 / 200 = 85%

Comparing this to the March cohort's Month-1 retention (94% vs. January's 92%) suggests recent onboarding or product changes may be improving early retention.

# Common mistakes

- Comparing cohorts of different sizes or from very different market conditions as if they were directly equivalent.
- Only looking at the most recent cohort's early numbers and declaring success before enough time has passed to know if retention holds.
- Mixing logo-based and revenue-based cohort retention in the same table without labeling which is which.
- Rebuilding cohort tables manually in spreadsheets without a consistent, automated definition of "cohort start date," causing drift between reports.

# Related metrics

- **NRR / GRR** — most rigorously measured at the cohort level rather than as a single blended figure.
- **Churn Rate** — cohort analysis reveals whether churn is concentrated in early tenure or spread evenly.
- **LTV** — cohort-based LTV, which lets churn vary by cohort age, is more accurate than a single blended LTV estimate.

# References

- ProfitWell SaaS metrics and retention resources (synthesized, not quoted)
- Reforge retention and growth essays (synthesized, not quoted)

*Note: cohort analysis is a methodology, not a metric with a single benchmark value — appropriate cohort windows and comparison periods vary by business model.*
