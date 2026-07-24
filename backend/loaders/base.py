"""DataSource abstraction — every revenue data source (CSV, Stripe, a real
database later) implements this interface. Nothing downstream (metrics
engine, chat tool) needs to know which concrete source is in use.
"""

from abc import ABC, abstractmethod

import pandas as pd


class DataSource(ABC):
    """A source of subscription/MRR data, normalized to one DataFrame shape:

    columns: date (Timestamp), mrr (float), status ("active"|"churned"),
             customer_id (str)

    One row = one customer's MRR contribution as of a given date. This is the
    only shape the rest of the app (RevenueMetricsEngine) depends on.
    """

    @abstractmethod
    def load_mrr_snapshots(self) -> pd.DataFrame:
        """Return the normalized (date, mrr, status, customer_id) DataFrame."""
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__
