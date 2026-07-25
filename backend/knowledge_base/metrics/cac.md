---
title: Customer Acquisition Cost
category: Metrics
metric: CAC
difficulty: Intermediate
source:
  - Winning by Design (synthesized)
  - Reforge (synthesized)
tags:
  - saas
  - unit-economics
  - sales-and-marketing
  - efficiency
---

# Definition

Customer Acquisition Cost (CAC) is the average cost of acquiring one new paying customer over a given period, calculated as total sales and marketing spend divided by the number of new customers acquired in that period.

# Why it matters

CAC is a core input to unit economics. On its own it says little — a $500 CAC could be excellent or terrible depending on what that customer is worth over their lifetime (LTV) and how quickly the cost is recovered (payback period). CAC becomes meaningful only when paired with those two companion metrics.

# Formula

```
CAC = Sales & Marketing Spend / New Customers Acquired
```

**Fully-loaded CAC** (recommended for serious unit-economics analysis) includes all attributable costs:

```
CAC = (S&M salaries + advertising + tools + agencies
       + commissions + attributable overhead) / New Paying Customers
```

**Blended vs. paid CAC:**

```
Blended CAC = Total S&M spend / All new customers
Paid CAC    = Paid acquisition spend / Customers from paid channels only
```

# Example

A company spends $50,000 on sales and marketing in a month and acquires 100 new paying customers.

```
CAC = $50,000 / 100 = $500 per customer
```

# Common mistakes

- Excluding sales salaries, commissions, or marketing software costs from a "fully-loaded" CAC figure.
- Dividing by trial signups or free-tier users instead of paying customers.
- Ignoring the lag between spend and the resulting customer (money spent in month N often converts to customers in month N+1 or later), which distorts month-by-month CAC if not adjusted for.
- Using a single blended CAC number to make channel-level decisions when paid and organic channels have very different costs.
- Comparing CAC across companies with fundamentally different go-to-market motions (self-serve/PLG vs. enterprise sales) as if they were equivalent.

# Related metrics

- **LTV** — customer lifetime value; CAC is only meaningful in the context of the LTV:CAC ratio.
- **CAC Payback** — the time (in months) needed to recover CAC from gross profit; a more actionable companion metric than CAC alone.
- **ARPU** — feeds into both LTV and payback calculations alongside CAC.

# References

- Winning by Design revenue architecture materials (synthesized, not quoted)
- Reforge growth and RevOps essays (synthesized, not quoted)

*Note: "acceptable" CAC values are entirely channel- and business-model-dependent and are not stated as fixed numbers here. What matters is the CAC relative to LTV and payback period, not CAC in isolation.*
