---
title: Stripe Documentation & Resources
type: Reference
source: Stripe
tags:
  - benchmarks
  - industry-reference
  - billing
  - saas
---

# About

Stripe is a payments and billing infrastructure provider whose documentation defines many of the practical, implementation-level concepts behind subscription billing — proration, billing intervals, invoicing, and revenue recognition mechanics that underpin how MRR/ARR are actually computed in production systems.

# Common topics covered

- Subscription billing mechanics (intervals, proration, trials, plan changes)
- Invoice and payment lifecycle (draft, open, paid, past_due, uncollectible)
- Revenue recognition concepts as they relate to billing events
- Webhook-driven billing event handling (subscription created/updated/canceled)
- Practical definitions of subscription statuses that map directly to how MRR should be calculated (e.g., which statuses count as "active" revenue)

# When to use

Use Stripe's documentation when you need to understand the mechanical, implementation-level details of how a subscription's billing state maps to metrics like MRR — for example, exactly which subscription statuses should be treated as active vs. churned, or how mid-cycle plan changes are prorated.

# Notes

Stripe's documentation is implementation-focused rather than benchmark-focused — it does not publish industry-wide "typical" metric values, so it should be used as a reference for billing mechanics and terminology, not for comparative benchmarks.

# Official resource

https://docs.stripe.com/billing
