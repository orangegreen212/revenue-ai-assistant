"""Seed the Stripe test-mode sandbox with a bit of activity, so it doesn't
sit frozen between demos.

This script is NOT part of the analytics pipeline — nothing in loaders/,
metrics/, rag/, or api/ imports it or depends on it running. It's a
standalone maintenance tool you run manually (or on your own schedule)
when you want the sandbox to look like an active business again.

Usage:
    python -m scripts.seed_sandbox
"""

import os
import random

import stripe
from dotenv import load_dotenv

load_dotenv()

FAKE_NAMES = ["Ava Kane", "Liam Cho", "Noor Patel", "Ivo Marek", "Sena Okafor"]


def _ensure_test_price() -> str:
    """Reuses an existing recurring test price if one exists, else creates one."""
    prices = stripe.Price.list(limit=10, active=True)
    for p in prices.auto_paging_iter():
        if p.get("recurring"):
            return p["id"]

    product = stripe.Product.create(name="Revenue AI — Demo Plan")
    price = stripe.Price.create(
        product=product["id"],
        unit_amount=random.choice([1900, 4900, 9900]),
        currency="usd",
        recurring={"interval": "month"},
    )
    return price["id"]


def seed(new_customers: int = 2, churn_one_existing: bool = True) -> None:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise SystemExit("STRIPE_SECRET_KEY is not set — add it to your .env first.")

    price_id = _ensure_test_price()

    for _ in range(new_customers):
        name = random.choice(FAKE_NAMES)
        customer = stripe.Customer.create(
            name=name,
            email=f"{name.lower().replace(' ', '.')}.{random.randint(1000,9999)}@example.com",
            payment_method="pm_card_visa",
            invoice_settings={"default_payment_method": "pm_card_visa"},
        )
        stripe.Subscription.create(
            customer=customer["id"],
            items=[{"price": price_id}],
        )
        print(f"Created subscription for {customer['id']} ({name})")

    if churn_one_existing:
        subs = stripe.Subscription.list(limit=20, status="active")
        active = list(subs.auto_paging_iter())
        if active:
            victim = random.choice(active)
            stripe.Subscription.cancel(victim["id"])
            print(f"Canceled subscription {victim['id']} (simulated churn)")


if __name__ == "__main__":
    seed()
