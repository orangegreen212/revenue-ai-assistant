"""Regenerate data/revenue_sample.csv with monthly snapshots ending at the
CURRENT month, so the CSV data source always looks "live" in demos instead
of being frozen at a fixed historical date.

This is a standalone maintenance script — nothing in loaders/, metrics/,
rag/, or api/ imports it. Run it whenever you want fresh-looking demo data:

    python -m scripts.generate_demo_data

It simulates a small but growing customer base with a bit of realistic
month-to-month churn and new-customer activity.
"""

import random
from datetime import date

import pandas as pd

OUTPUT_PATH = "data/revenue_sample.csv"
MONTHS_OF_HISTORY = 9
STARTING_CUSTOMERS = [
    ("CUST_001", 150.0),
    ("CUST_002", 200.0),
    ("CUST_003", 50.0),
]


def month_start(d: date) -> date:
    return d.replace(day=1)


def add_months(d: date, n: int) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def generate(months: int = MONTHS_OF_HISTORY) -> pd.DataFrame:
    today = month_start(date.today())
    start_month = add_months(today, -(months - 1))

    customers = {cid: mrr for cid, mrr in STARTING_CUSTOMERS}
    next_id = len(customers) + 1
    rows = []

    for i in range(months):
        current_month = add_months(start_month, i)

        # Occasionally add a new customer
        if random.random() < 0.6:
            cid = f"CUST_{next_id:03d}"
            customers[cid] = random.choice([50.0, 100.0, 150.0, 200.0, 300.0])
            rows.append({"date": current_month, "mrr": customers[cid], "status": "new", "customer_id": cid})
            next_id += 1

        # Occasionally churn an existing customer (never on the first month)
        if i > 0 and len(customers) > 1 and random.random() < 0.15:
            churned_id = random.choice(list(customers.keys()))
            rows.append({"date": current_month, "mrr": 0.0, "status": "churned", "customer_id": churned_id})
            del customers[churned_id]

        # Everyone else stays active this month (skip customers already logged above this month)
        logged_this_month = {r["customer_id"] for r in rows if r["date"] == current_month}
        for cid, mrr in customers.items():
            if cid not in logged_this_month:
                rows.append({"date": current_month, "mrr": mrr, "status": "active", "customer_id": cid})

    df = pd.DataFrame(rows).sort_values(["date", "customer_id"]).reset_index(drop=True)
    return df


def main():
    df = generate()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} rows spanning {df['date'].min()} .. {df['date'].max()} to '{OUTPUT_PATH}'.")


if __name__ == "__main__":
    main()
