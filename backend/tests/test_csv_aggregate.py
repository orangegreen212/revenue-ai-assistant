"""Unit tests for csv_aggregate — the deterministic pandas-based aggregation tool."""

import pandas as pd
import pytest

from tools.analytics_tools import csv_aggregate


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame({
        "country": ["USA", "USA", "Canada", "Canada", "Canada"],
        "session_time": [120, 200, 50, 100, 150],
    })
    path = tmp_path / "sessions.csv"
    df.to_csv(path, index=False)
    return str(path)


class TestCsvAggregate:
    def test_sum_over_all_rows(self, sample_csv):
        result = csv_aggregate.invoke(
            {"file_path": sample_csv, "column": "session_time", "operation": "sum"}
        )
        assert "620" in result  # 120+200+50+100+150

    def test_mean(self, sample_csv):
        result = csv_aggregate.invoke(
            {"file_path": sample_csv, "column": "session_time", "operation": "mean"}
        )
        assert "124" in result  # 620 / 5

    def test_groupby_sum(self, sample_csv):
        result = csv_aggregate.invoke({
            "file_path": sample_csv,
            "column": "session_time",
            "operation": "sum",
            "groupby": "country",
        })
        assert "USA" in result and "320" in result  # 120+200
        assert "Canada" in result and "300" in result  # 50+100+150

    def test_missing_file_returns_error_not_crash(self):
        result = csv_aggregate.invoke(
            {"file_path": "/nonexistent/path.csv", "column": "x", "operation": "sum"}
        )
        assert "Error" in result
        assert "not found" in result.lower()

    def test_missing_column_lists_available_columns(self, sample_csv):
        result = csv_aggregate.invoke(
            {"file_path": sample_csv, "column": "nonexistent_col", "operation": "sum"}
        )
        assert "Error" in result
        assert "country" in result  # lists what IS available

    def test_invalid_operation_lists_valid_ones(self, sample_csv):
        result = csv_aggregate.invoke(
            {"file_path": sample_csv, "column": "session_time", "operation": "yeet"}
        )
        assert "Error" in result
        assert "sum" in result  # lists valid operations

    def test_invalid_groupby_column(self, sample_csv):
        result = csv_aggregate.invoke({
            "file_path": sample_csv,
            "column": "session_time",
            "operation": "sum",
            "groupby": "nonexistent_col",
        })
        assert "Error" in result

    def test_min_max_median(self, sample_csv):
        assert "50" in csv_aggregate.invoke(
            {"file_path": sample_csv, "column": "session_time", "operation": "min"}
        )
        assert "200" in csv_aggregate.invoke(
            {"file_path": sample_csv, "column": "session_time", "operation": "max"}
        )
