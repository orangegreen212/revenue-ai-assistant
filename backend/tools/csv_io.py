"""Shared file-loading helper, used by csv_tools.py and financial_statement.py.

Split out on its own so financial_statement.py doesn't need to import from
csv_tools.py (which itself imports from financial_statement.py) — avoids a
circular import between the two.
"""

import os
from typing import Optional

import pandas as pd


def load_csv(file_path: str) -> tuple[Optional["pd.DataFrame"], Optional[str]]:
    """Shared file-loading boilerplate for csv_aggregate, csv_row_sum, get_csv_agent,
    and analyze_financial_statement.

    Returns (dataframe, None) on success or (None, error_message) on failure.
    """
    if not os.path.exists(file_path):
        return None, f"Error: file not found at '{file_path}'."
    try:
        return pd.read_csv(file_path), None
    except Exception as exc:  # noqa: BLE001
        return None, f"Error reading CSV at '{file_path}': {exc}"
