"""RevenueMetricsEngine — takes the normalized (date, mrr, status,
customer_id) DataFrame from ANY DataSource and computes current-state KPIs.

This module has zero knowledge of Stripe, CSVs, or anything else — it only
knows the DataFrame contract defined in loaders/base.py. Swapping the data
source never requires touching this file.
"""

from datetime import datetime, timezone

import pandas as pd

from loaders.base import DataSource


class RevenueMetricsEngine:
    def __init__(self, source: DataSource):
        self.source = source

    def compute(self) -> dict:
        df = self.source.load_mrr_snapshots()
        if df.empty:
            raise ValueError(f"{self.source.name()} returned no data to compute metrics from.")

        months = sorted(df["date"].unique())
        latest_month = months[-1]
        prev_month = months[-2] if len(months) > 1 else None

        latest = df[df["date"] == latest_month]
        current_mrr = float(latest.loc[latest["status"] != "churned", "mrr"].sum())
        active_customers = int((latest["status"] != "churned").sum())

        metrics = {
            "source": self.source.name(),
            "as_of": pd.Timestamp(latest_month).strftime("%Y-%m-%d"),
            "mrr": round(current_mrr, 2),
            "arr": round(current_mrr * 12, 2),
            "active_customers": active_customers,
            "arpu": round(current_mrr / active_customers, 2) if active_customers else None,
        }

        if prev_month is not None:
            prev = df[df["date"] == prev_month]
            prev_mrr = float(prev.loc[prev["status"] != "churned", "mrr"].sum())
            prev_customers = set(prev.loc[prev["status"] != "churned", "customer_id"])
            curr_customers = set(latest.loc[latest["status"] != "churned", "customer_id"])
            churned_customers = prev_customers - curr_customers
            new_customers = curr_customers - prev_customers

            metrics["mrr_prev_month"] = round(prev_mrr, 2)
            metrics["mom_mrr_growth_pct"] = (
                round((current_mrr - prev_mrr) / prev_mrr * 100, 2) if prev_mrr else None
            )
            metrics["logo_churn_rate_pct"] = (
                round(len(churned_customers) / len(prev_customers) * 100, 2)
                if prev_customers
                else None
            )
            metrics["new_customers"] = len(new_customers)

        metrics["generated_at"] = datetime.now(timezone.utc).isoformat()
        return metrics
