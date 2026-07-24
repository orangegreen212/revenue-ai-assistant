"""Snapshot service — picks a DataSource (CSV or Stripe, via DATA_SOURCE env
var), runs it through RevenueMetricsEngine, and persists the result.

This is the only place that knows how to choose a data source. Everything
downstream (the get_live_metric tool, the /api/live-metrics endpoint) just
reads the persisted snapshot — it doesn't know or care whether the numbers
came from a CSV or from Stripe.
"""

import json
import os

from loaders.csv_loader import CsvLoader
from loaders.stripe_loader import StripeSnapshotLoader
from metrics.revenue_metrics import RevenueMetricsEngine

SNAPSHOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "live_metrics.json")


def get_data_source():
    """DATA_SOURCE=stripe uses the Stripe sandbox; anything else (or unset)
    falls back to the CSV loader — this is the one branch in the whole app
    that picks a concrete DataSource implementation."""
    choice = os.getenv("DATA_SOURCE", "csv").strip().lower()
    if choice == "stripe":
        return StripeSnapshotLoader()
    return CsvLoader()


def refresh() -> dict:
    source = get_data_source()
    engine = RevenueMetricsEngine(source)
    metrics = engine.compute()

    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return metrics


def read_snapshot() -> dict | None:
    if not os.path.exists(SNAPSHOT_PATH):
        return None
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    result = refresh()
    print(json.dumps(result, indent=2))
