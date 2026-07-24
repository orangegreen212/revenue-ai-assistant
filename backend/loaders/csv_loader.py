"""CsvLoader — reads MRR snapshots from a local CSV. Used as the default /
fallback data source, and for local development without Stripe credentials.
"""

import os

import pandas as pd

from loaders.base import DataSource

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "revenue_sample.csv")


class CsvLoader(DataSource):
    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path

    def load_mrr_snapshots(self) -> pd.DataFrame:
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"CSV data source not found at '{self.path}'.")
        return pd.read_csv(self.path, parse_dates=["date"])
