---
title: Pirate Metrics (AARRR)
category: Frameworks
metric: null
difficulty: Beginner
source:
  - Reforge (synthesized)
  - Widely-used growth framework popularized by Dave McClure
tags:
  - growth
  - funnel
  - product-led-growth
  - saas
---

# Definition

Pirate Metrics (AARRR) is a framework that breaks the customer lifecycle into five stages — **A**cquisition, **A**ctivation, **R**etention, **R**eferral, **R**evenue — giving product and growth teams a shared vocabulary for diagnosing where users drop off or where growth investment should focus.

# Why it matters

Many teams over-focus on the top of the funnel (traffic, signups) without realizing that activation or retention is the actual bottleneck. AARRR forces a full-funnel view: acquiring more users is wasted effort if most of them never activate or never come back.

# Formula

Each stage has its own core question and metric rather than a single combined formula:

| Stage | Core Question | Example Metric |
|---|---|---|
| Acquisition | How do users find us? | Visitors, signups by channel |
| Activation | Do users have a good first experience? | % reaching "aha moment" / time-to-value |
| Retention | Do users come back? | Day-30 retention, monthly churn |
| Referral | Do users tell others? | Viral coefficient, referral rate |
| Revenue | Do users pay? | Conversion to paid, ARPU |

A simplified funnel conversion view:

```
Stage Conversion Rate = Users reaching Stage N / Users reaching Stage N-1
```

# Example

Out of 10,000 monthly visitors: 1,000 sign up (10% acquisition-to-signup), 400 reach the activation milestone (40% activation rate), 150 are still active 30 days later (37.5% Day-30 retention), 30 refer another user (20% referral rate among retained users), and 60 convert to paid (40% of retained users monetize).

# Common mistakes

- Optimizing acquisition spend while activation is the real bottleneck — more traffic into a broken first-run experience just produces more churned signups.
- Defining "activation" too vaguely (e.g., "logged in") instead of tying it to a specific, meaningful action that correlates with long-term retention.
- Treating referral as an afterthought rather than instrumenting it as its own measurable stage.
- Using AARRR as a one-time framework rather than revisiting funnel conversion rates regularly as the product and channels evolve.

# Related metrics

- **Sales Funnel** — the B2B/sales-motion equivalent of the acquisition and activation stages.
- **Cohort Analysis** — the standard method for measuring the Retention stage accurately over time.
- **Churn Rate** — the inverse of the Retention stage.
- **ARPU** — a common way to quantify the Revenue stage.

# References

- Reforge growth frameworks (synthesized, not quoted)
- The AARRR framework, originally popularized by investor Dave McClure (500 Startups); widely adapted since across the growth and product community.

*Note: what counts as "good" conversion at each AARRR stage varies enormously by product category (B2B vs. B2C, PLG vs. sales-led) — no universal targets are stated here.*
