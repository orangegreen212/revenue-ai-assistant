"""Unit tests for the loaders/metrics layer — verifies the DataSource
abstraction and RevenueMetricsEngine compute the right numbers regardless
of which concrete loader supplies the data.
"""

import pandas as pd
import pytest

from loaders.base import DataSource
from loaders.csv_loader import CsvLoader
from metrics.revenue_metrics import RevenueMetricsEngine


class FakeSource(DataSource):
    """An in-memory DataSource for testing RevenueMetricsEngine without
    touching any file or external API — this is exactly the point of the
    DataSource abstraction: the engine shouldn't care where data comes from.
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def load_mrr_snapshots(self) -> pd.DataFrame:
        return self._df


def _two_month_frame():
    return pd.DataFrame([
        {"date": "2026-06-01", "mrr": 100, "status": "active", "customer_id": "A"},
        {"date": "2026-06-01", "mrr": 200, "status": "active", "customer_id": "B"},
        {"date": "2026-07-01", "mrr": 100, "status": "active", "customer_id": "A"},
        {"date": "2026-07-01", "mrr": 200, "status": "active", "customer_id": "B"},
        {"date": "2026-07-01", "mrr": 150, "status": "new", "customer_id": "C"},
    ]).assign(date=lambda d: pd.to_datetime(d["date"]))


class TestRevenueMetricsEngine:
    def test_computes_current_mrr_and_arr(self):
        engine = RevenueMetricsEngine(FakeSource(_two_month_frame()))
        result = engine.compute()
        assert result["mrr"] == 450  # 100 + 200 + 150 in the latest month
        assert result["arr"] == 5400  # 450 * 12

    def test_reports_which_source_was_used(self):
        engine = RevenueMetricsEngine(FakeSource(_two_month_frame()))
        result = engine.compute()
        assert result["source"] == "FakeSource"

    def test_active_customers_excludes_churned(self):
        df = pd.DataFrame([
            {"date": "2026-07-01", "mrr": 100, "status": "active", "customer_id": "A"},
            {"date": "2026-07-01", "mrr": 0, "status": "churned", "customer_id": "B"},
        ]).assign(date=lambda d: pd.to_datetime(d["date"]))
        engine = RevenueMetricsEngine(FakeSource(df))
        result = engine.compute()
        assert result["active_customers"] == 1

    def test_mom_growth_and_new_customers(self):
        engine = RevenueMetricsEngine(FakeSource(_two_month_frame()))
        result = engine.compute()
        # prev month mrr = 300, current = 450 -> +50%
        assert result["mom_mrr_growth_pct"] == 50.0
        assert result["new_customers"] == 1  # customer C is new in July

    def test_empty_source_raises_clear_error(self):
        engine = RevenueMetricsEngine(FakeSource(pd.DataFrame(columns=["date", "mrr", "status", "customer_id"])))
        with pytest.raises(ValueError):
            engine.compute()

    def test_arpu_handles_zero_active_customers(self):
        df = pd.DataFrame([
            {"date": "2026-07-01", "mrr": 0, "status": "churned", "customer_id": "A"},
        ]).assign(date=lambda d: pd.to_datetime(d["date"]))
        engine = RevenueMetricsEngine(FakeSource(df))
        result = engine.compute()
        assert result["arpu"] is None  # must not divide by zero


class TestCsvLoader:
    def test_loads_csv_into_expected_shape(self, tmp_path):
        csv_path = tmp_path / "revenue.csv"
        csv_path.write_text(
            "date,mrr,status,customer_id\n2026-07-01,100.0,active,CUST_001\n"
        )
        loader = CsvLoader(path=str(csv_path))
        df = loader.load_mrr_snapshots()
        assert list(df.columns) == ["date", "mrr", "status", "customer_id"]
        assert len(df) == 1

    def test_missing_file_raises_clear_error(self):
        loader = CsvLoader(path="/nonexistent/revenue.csv")
        with pytest.raises(FileNotFoundError):
            loader.load_mrr_snapshots()

    def test_is_a_datasource(self):
        # Enforces the DataSource contract at the type level — this is what
        # lets snapshot_service swap CsvLoader for StripeSnapshotLoader freely.
        assert isinstance(CsvLoader(path="anything.csv"), DataSource)
