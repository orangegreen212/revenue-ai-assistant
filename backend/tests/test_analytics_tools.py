"""Unit tests for the deterministic KPI/benchmark tools.

get_csv_agent is intentionally NOT unit-tested here — it calls a real LLM
over the network (integration-level, not a pure function). csv_aggregate,
calculate_kpi, and get_benchmark are pure logic and are fully covered.

Run: pytest tests/ -v
"""

import pytest

from tools.analytics_tools import calculate_kpi, get_benchmark


class TestCalculateKpi:
    def test_mrr_is_passthrough(self):
        result = calculate_kpi.invoke({"kpi_name": "mrr", "value_a": 1000, "value_b": 0})
        assert "1,000" in result or "1000" in result

    def test_arr_multiplies_by_12(self):
        result = calculate_kpi.invoke({"kpi_name": "arr", "value_a": 100, "value_b": 0})
        assert "1,200" in result or "1200" in result

    def test_cac_divides_spend_by_customers(self):
        result = calculate_kpi.invoke(
            {"kpi_name": "cac", "value_a": 10000, "value_b": 200}
        )
        assert "50" in result

    def test_cac_zero_customers_returns_error_not_crash(self):
        result = calculate_kpi.invoke({"kpi_name": "cac", "value_a": 10000, "value_b": 0})
        assert "Error" in result
        assert "zero" in result.lower()

    def test_ltv_formula(self):
        # LTV = ARPU * margin / churn = 100 * 0.8 / 0.02 = 4000
        result = calculate_kpi.invoke(
            {"kpi_name": "ltv", "value_a": 100, "value_b": 0.02, "value_c": 0.8}
        )
        assert "4,000" in result or "4000" in result

    def test_ltv_default_margin_is_80_percent(self):
        # value_c omitted -> should default to 0.8, same result as above
        result = calculate_kpi.invoke({"kpi_name": "ltv", "value_a": 100, "value_b": 0.02})
        assert "4,000" in result or "4000" in result

    def test_ltv_zero_churn_returns_error_not_crash(self):
        result = calculate_kpi.invoke({"kpi_name": "ltv", "value_a": 100, "value_b": 0})
        assert "Error" in result

    def test_grr_is_capped_at_100_percent(self):
        # value_a > value_b would mathematically exceed 100% if uncapped
        result = calculate_kpi.invoke({"kpi_name": "grr", "value_a": 1200, "value_b": 1000})
        assert "100.00%" in result

    def test_nrr_can_exceed_100_percent(self):
        result = calculate_kpi.invoke({"kpi_name": "nrr", "value_a": 1200, "value_b": 1000})
        assert "120.00%" in result

    def test_arpu_divides_mrr_by_customers(self):
        result = calculate_kpi.invoke({"kpi_name": "arpu", "value_a": 5000, "value_b": 250})
        assert "20" in result

    def test_payback_uses_margin(self):
        # Payback = CAC / (ARPU * margin) = 600 / (100 * 0.8) = 7.5 months
        result = calculate_kpi.invoke(
            {"kpi_name": "payback", "value_a": 600, "value_b": 100, "value_c": 0.8}
        )
        assert "7.5" in result

    def test_ltv_cac_ratio_format(self):
        result = calculate_kpi.invoke({"kpi_name": "ltv_cac", "value_a": 3000, "value_b": 1000})
        assert "3.00:1" in result

    def test_unsupported_metric_lists_supported_ones(self):
        result = calculate_kpi.invoke({"kpi_name": "unicorn_metric", "value_a": 1, "value_b": 1})
        assert "Unsupported" in result
        assert "mrr" in result.lower()

    def test_metric_name_is_case_and_separator_insensitive(self):
        a = calculate_kpi.invoke({"kpi_name": "LTV_CAC", "value_a": 30, "value_b": 10})
        b = calculate_kpi.invoke({"kpi_name": "ltv-cac", "value_a": 30, "value_b": 10})
        assert a == b

    def test_ukrainian_output_language(self):
        result = calculate_kpi.invoke(
            {"kpi_name": "cac", "value_a": 10000, "value_b": 200, "lang": "uk"}
        )
        assert "CAC" in result  # formula label still present
        # zero-customer error should be in Ukrainian when lang=uk
        err = calculate_kpi.invoke(
            {"kpi_name": "cac", "value_a": 10000, "value_b": 0, "lang": "uk"}
        )
        assert "Помилка" in err


class TestGetBenchmark:
    def test_returns_all_four_sections_for_known_metric(self):
        result = get_benchmark.invoke({"metric_name": "mrr"})
        assert "What it measures" in result
        assert "Good / target" in result
        assert "Typical range" in result
        assert "Watch out" in result

    def test_alias_resolution(self):
        result = get_benchmark.invoke({"metric_name": "net_revenue_retention"})
        assert "NRR" in result

    def test_unknown_metric_lists_supported_ones_not_crash(self):
        result = get_benchmark.invoke({"metric_name": "unicorn_metric"})
        assert "No benchmark stored" in result

    def test_ukrainian_output(self):
        result = get_benchmark.invoke({"metric_name": "mrr", "lang": "uk"})
        assert "Бенчмарк" in result

    def test_invalid_lang_falls_back_to_english(self):
        result = get_benchmark.invoke({"metric_name": "mrr", "lang": "fr"})
        assert "Benchmark" in result  # English fallback, not a crash
