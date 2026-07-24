"""StripeSnapshotLoader — pulls the current state of a Stripe (test-mode)
account via the real Stripe API and normalizes it into DataFrames.

Requires STRIPE_SECRET_KEY (a sk_test_... key) in the environment.

Stripe test-mode data does not change on its own — see scripts/seed_sandbox.py
for a *separate* tool that creates test activity so the sandbox behaves like
a business over time. This loader has no dependency on that script; it just
reads whatever state Stripe currently has, same as it would for a real
production Stripe account.
"""

import os

import pandas as pd

from loaders.base import DataSource


class StripeSnapshotLoader(DataSource):
    def __init__(self, api_key: str | None = None):
        import stripe  # imported lazily — CSV-only setups shouldn't need this package installed

        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY is not set.")
        self._stripe = stripe
        self._stripe.api_key = self.api_key

    # ---- individual object DataFrames (for richer analysis later) ----

    def customers_df(self) -> pd.DataFrame:
        rows = [
            {"customer_id": c["id"], "email": c.get("email"), "created": pd.Timestamp.fromtimestamp(c["created"])}
            for c in self._stripe.Customer.list(limit=100).auto_paging_iter()
        ]
        return pd.DataFrame(rows)

    def subscriptions_df(self) -> pd.DataFrame:
        rows = []
        for sub in self._stripe.Subscription.list(limit=100, status="all").auto_paging_iter():
            items = sub["items"]["data"]
            if not items:
                continue
            price = items[0]["price"]
            rows.append({
                "subscription_id": sub["id"],
                "customer_id": sub["customer"],
                "status": sub["status"],
                "unit_amount": (price.get("unit_amount") or 0) / 100,
                "interval": (price.get("recurring") or {}).get("interval", "month"),
                "quantity": items[0].get("quantity", 1),
                "current_period_start": pd.Timestamp.fromtimestamp(sub["current_period_start"]),
            })
        return pd.DataFrame(rows)

    def invoices_df(self) -> pd.DataFrame:
        rows = [
            {
                "invoice_id": inv["id"],
                "customer_id": inv["customer"],
                "amount_paid": (inv.get("amount_paid") or 0) / 100,
                "status": inv["status"],
                "created": pd.Timestamp.fromtimestamp(inv["created"]),
            }
            for inv in self._stripe.Invoice.list(limit=100).auto_paging_iter()
        ]
        return pd.DataFrame(rows)

    def refunds_df(self) -> pd.DataFrame:
        rows = [
            {
                "refund_id": r["id"],
                "amount": (r.get("amount") or 0) / 100,
                "created": pd.Timestamp.fromtimestamp(r["created"]),
            }
            for r in self._stripe.Refund.list(limit=100).auto_paging_iter()
        ]
        return pd.DataFrame(rows)

    def products_df(self) -> pd.DataFrame:
        rows = [
            {"product_id": p["id"], "name": p.get("name")}
            for p in self._stripe.Product.list(limit=100).auto_paging_iter()
        ]
        return pd.DataFrame(rows)

    def prices_df(self) -> pd.DataFrame:
        rows = [
            {
                "price_id": p["id"],
                "product_id": p.get("product"),
                "unit_amount": (p.get("unit_amount") or 0) / 100,
                "interval": (p.get("recurring") or {}).get("interval"),
            }
            for p in self._stripe.Price.list(limit=100).auto_paging_iter()
        ]
        return pd.DataFrame(rows)

    # ---- the one DataFrame the rest of the app actually depends on ----

    def load_mrr_snapshots(self) -> pd.DataFrame:
        """Normalizes subscriptions into the same (date, mrr, status,
        customer_id) shape CsvLoader produces — this is the DataSource
        contract, so RevenueMetricsEngine doesn't care where it came from.
        """
        subs_df = self.subscriptions_df()
        if subs_df.empty:
            return pd.DataFrame(columns=["date", "mrr", "status", "customer_id"])

        def monthly_mrr(row):
            amount = row["unit_amount"] * row["quantity"]
            if row["interval"] == "year":
                return amount / 12
            if row["interval"] == "week":
                return amount * 52 / 12
            return amount

        subs_df["mrr"] = subs_df.apply(monthly_mrr, axis=1)
        subs_df["status"] = subs_df["status"].apply(
            lambda s: "churned" if s in {"canceled", "unpaid", "incomplete_expired"} else "active"
        )
        subs_df["date"] = subs_df["current_period_start"].dt.normalize()

        return subs_df[["date", "mrr", "status", "customer_id"]]
