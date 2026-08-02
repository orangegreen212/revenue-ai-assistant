"""Backward-compatible facade over the split analytics tool modules.

This file used to hold ~1600 lines of unrelated tools in one place (CSV
aggregation, KPI math, SQL templates, and a whole financial-statement parser).
It's now split by domain:

    tools/csv_io.py               - shared CSV-loading helper
    tools/csv_tools.py            - csv_aggregate, csv_row_sum, get_csv_agent
    tools/kpi.py                  - calculate_kpi, get_benchmark, get_live_metric
    tools/sql.py                  - generate_sql
    tools/financial_statement.py  - detect/normalize/analyze financial statements

Everything below is re-exported here, unchanged, so existing imports
(``from tools.analytics_tools import ...`` in rag_core.py, api/main.py, and
the test suite) keep working without any call-site changes.
"""

from tools.csv_io import load_csv as _load_csv
from tools.csv_tools import csv_aggregate, csv_row_sum, get_csv_agent
from tools.financial_statement import (
    _infer_financial_statement_args,
    analyze_financial_statement,
    detect_financial_statement,
    infer_financial_statement_args,
    normalize_financial_dataframe,
)
from tools.kpi import _KPI_BENCHMARKS, calculate_kpi, get_benchmark, get_live_metric
from tools.sql import generate_sql

__all__ = [
    "csv_aggregate",
    "csv_row_sum",
    "get_csv_agent",
    "calculate_kpi",
    "get_benchmark",
    "get_live_metric",
    "generate_sql",
    "analyze_financial_statement",
    "detect_financial_statement",
    "normalize_financial_dataframe",
    "infer_financial_statement_args",
]
