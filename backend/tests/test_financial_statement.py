"""Unit tests for financial-statement detection, normalization, and analysis.

Uses small artificial Balance Sheet dataframes — no LLM / network calls.

Run: pytest tests/test_financial_statement.py -v
"""

import pandas as pd
import pytest

from tools.analytics_tools import (
    analyze_financial_statement,
    detect_financial_statement,
    normalize_financial_dataframe,
)


@pytest.fixture
def balance_sheet_df() -> pd.DataFrame:
    """Minimal Excel-style Balance Sheet export (Unnamed label col, accounting text)."""
    return pd.DataFrame(
        {
            "Unnamed: 0": [
                "Balance Sheet",
                "Cash",
                "Receivables",
                "Inventory",
                "Current Assets",
                "Property Plant and Equipment",
                "Non-current Assets",
                "Total Assets",
                "Accounts Payable",
                "Long-term Debt",
                "Total Liabilities",
                "Shareholders Equity",
            ],
            "2023": [
                "",
                "$1,000",
                "$2,000",
                "$500",
                "$3,500",
                "$1,500",
                "$1,500",
                "$5,000",
                "$1,200",
                "$1,800",
                "$3,000",
                "$2,000",
            ],
            "2024": [
                "",
                "$1,200",
                "$2,100",
                "$400",
                "$3,700",
                "$1,800",
                "$1,800",
                "$5,500",
                "$1,300",
                "$1,900",
                "$3,200",
                "$2,300",
            ],
            "Unnamed: 3": [None] * 12,
        }
    )


@pytest.fixture
def balance_sheet_csv(balance_sheet_df, tmp_path) -> str:
    path = tmp_path / "balance_sheet.csv"
    balance_sheet_df.to_csv(path, index=False)
    return str(path)


class TestDetectAndNormalize:
    def test_detects_balance_sheet(self, balance_sheet_df):
        assert detect_financial_statement(balance_sheet_df) == "Balance Sheet"

    def test_normalize_cleans_unnamed_and_accounting_numbers(self, balance_sheet_df):
        out = normalize_financial_dataframe(balance_sheet_df)
        assert "Item" in out.columns
        assert "Unnamed: 3" not in out.columns
        assert list(out.columns) == ["Item", "2023", "2024"]
        cash = out.loc[out["Item"] == "Cash"].iloc[0]
        assert cash["2023"] == 1000.0
        assert cash["2024"] == 1200.0


class TestLineLookups:
    def test_total_assets(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "line_lookup",
                "line_item": "Total Assets",
            }
        )
        assert "Balance Sheet" in result
        assert "Total Assets" in result
        assert "5,000.00" in result
        assert "5,500.00" in result

    def test_current_assets(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "yearly_values",
                "line_item": "Current Assets",
                "year": "2024",
            }
        )
        assert "Current Assets" in result
        assert "3,700.00" in result

    def test_non_current_assets(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "line_lookup",
                "line_item": "Non-current Assets",
            }
        )
        assert "Non-current Assets" in result
        assert "1,500.00" in result
        assert "1,800.00" in result

    def test_liabilities(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "line_lookup",
                "line_item": "Total Liabilities",
            }
        )
        assert "Total Liabilities" in result
        assert "3,000.00" in result
        assert "3,200.00" in result

    def test_equity(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "year_comparison",
                "line_item": "Shareholders Equity",
                "year_a": "2023",
                "year_b": "2024",
            }
        )
        assert "Shareholders Equity" in result
        assert "2,000.00" in result
        assert "2,300.00" in result
        assert "300.00" in result  # change


class TestValidation:
    def test_current_assets_equal_sum_of_components(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "total_validation",
                "total_line": "Current Assets",
                "component_lines": "Cash, Receivables, Inventory",
            }
        )
        assert "PASS" in result
        assert "FAIL" not in result
        assert "3,500.00" in result
        assert "3,700.00" in result

    def test_total_assets_equal_current_plus_non_current(self, balance_sheet_csv):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "total_validation",
                "total_line": "Total Assets",
                "component_lines": "Current Assets, Non-current Assets",
                "year": "2023",
            }
        )
        assert "2023" in result
        assert "PASS" in result
        assert "5,000.00" in result

    def test_accounting_equation_assets_vs_liabilities_plus_equity(
        self, balance_sheet_csv
    ):
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "total_validation",
                "total_line": "Total Assets",
                "component_lines": "Total Liabilities, Shareholders Equity",
            }
        )
        assert "PASS" in result
        assert "FAIL" not in result

    def test_validation_fails_when_components_do_not_add_up(self, tmp_path):
        df = pd.DataFrame(
            {
                "Item": ["Cash", "Total Current Assets"],
                "2023": [100, 999],
            }
        )
        path = tmp_path / "bad_total.csv"
        df.to_csv(path, index=False)
        result = analyze_financial_statement.invoke(
            {
                "file_path": str(path),
                "operation": "total_validation",
                "total_line": "Total Current Assets",
                "component_lines": "Cash",
            }
        )
        assert "FAIL" in result


class TestYoyGrowth:
    def test_total_assets_yoy_growth(self, balance_sheet_csv):
        # (5500 - 5000) / 5000 = 10%
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "yoy_growth",
                "line_item": "Total Assets",
                "year_a": "2023",
                "year_b": "2024",
            }
        )
        assert "Total Assets" in result
        assert "5,000.00" in result
        assert "5,500.00" in result
        assert "500.00" in result
        assert "10.00%" in result

    def test_equity_yoy_growth_defaults_to_latest_two_years(self, balance_sheet_csv):
        # (2300 - 2000) / 2000 = 15%
        result = analyze_financial_statement.invoke(
            {
                "file_path": balance_sheet_csv,
                "operation": "yoy_growth",
                "line_item": "Shareholders Equity",
            }
        )
        assert "Shareholders Equity" in result
        assert "15.00%" in result
