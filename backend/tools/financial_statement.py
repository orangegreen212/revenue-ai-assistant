"""Financial-statement detection, normalization, and analysis (Balance Sheet,
Income Statement, Cash Flow). Split out of the former monolithic
analytics_tools.py so this ~900-line domain gets its own file.
"""

import re
from typing import Optional

import pandas as pd
from langchain_core.tools import tool

from tools.csv_io import load_csv

_BALANCE_SHEET_KEYWORDS = (
    "balance sheet",
    "statement of financial position",
    "total assets",
    "total liabilities",
    "shareholders' equity",
    "stockholders' equity",
    "current assets",
    "non-current assets",
    "current liabilities",
)

_INCOME_STATEMENT_KEYWORDS = (
    "income statement",
    "statement of operations",
    "profit and loss",
    "profit & loss",
    "p&l",
    "net income",
    "operating income",
    "gross profit",
    "cost of goods sold",
    "cost of sales",
    "revenue",
    "net sales",
)

_CASH_FLOW_KEYWORDS = (
    "cash flow",
    "cash flows",
    "statement of cash flows",
    "operating activities",
    "investing activities",
    "financing activities",
    "net increase in cash",
    "net decrease in cash",
    "cash and cash equivalents",
)


def _dataframe_text_blob(df: "pd.DataFrame") -> str:
    """Flatten column names and a sample of cell values into one searchable string."""
    parts = [str(c) for c in df.columns]
    sample = df.head(80).astype(str).values.flatten()
    parts.extend(str(v) for v in sample if str(v).strip() and str(v).lower() != "nan")
    return " ".join(parts).lower()


def _count_keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for kw in keywords if kw in text)


def detect_financial_statement(df: "pd.DataFrame") -> Optional[str]:
    """Detect whether *df* looks like a Balance Sheet, Income Statement, or Cash Flow.

    Returns one of ``"Balance Sheet"``, ``"Income Statement"``, ``"Cash Flow"``,
    or ``None`` when no statement type can be confidently identified.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None

    text = _dataframe_text_blob(df)
    scores = {
        "Balance Sheet": _count_keyword_hits(text, _BALANCE_SHEET_KEYWORDS),
        "Income Statement": _count_keyword_hits(text, _INCOME_STATEMENT_KEYWORDS),
        "Cash Flow": _count_keyword_hits(text, _CASH_FLOW_KEYWORDS),
    }

    best_label, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return None

    # Require a clear winner when two types tie or nearly tie.
    ranked = sorted(scores.values(), reverse=True)
    if len(ranked) > 1 and ranked[0] == ranked[1]:
        return None

    return best_label


def _parse_accounting_number(value) -> object:
    """Convert Excel/accounting-style cell text into a float, or leave as-is.

    Handles currency symbols, thousands separators, parenthetical negatives,
    trailing minus signs, and common dash/blank placeholders for zero/missing.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NA
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "na"}:
        return pd.NA

    # Em/en dashes and lone hyphens often mean blank or zero in statements.
    if text in {"-", "–", "—", "−"}:
        return pd.NA

    cleaned = (
        text.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("₴", "")
    )

    # Accounting negative: (1,234.56) -> -1234.56
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]

    # Trailing minus: 1234.56- -> -1234.56
    if cleaned.endswith("-") and cleaned.count("-") == 1:
        cleaned = "-" + cleaned[:-1]

    try:
        return float(cleaned)
    except ValueError:
        return value


def _extract_year_number(name: object) -> Optional[int]:
    """Extract a valid year from a string, strictly distinguishing from financial amounts."""
    if name is None or pd.isna(name):
        return None
    
    s = str(name).strip()
    
    # 1. Check if the string is just a numeric value (likely an amount, not a header year).
    # Ignore values outside 1950-2050 to prevent treating "$2096.00" as the year 2096.
    clean_num = s.replace(",", "").replace("$", "").replace(" ", "")
    try:
        val = float(clean_num)
        # If it's perfectly an integer in the year range, it might actually be a year
        if val.is_integer() and 1950 <= val <= 2050:
            return int(val)
        # If it's any other number (e.g. 2096.0), it's financial data, NOT a year header
        if val > 1000 or val < -1000:
            return None
    except ValueError:
        pass

    # 2. It's a string like "2024-09-30", "FY2024", etc. Look for 4 digits.
    # Using negative lookbehind/lookahead to avoid matching mid-decimal (e.g. 1.2024)
    match = re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", s)
    if match:
        y = int(match.group(1))
        if 1950 <= y <= 2050:
            return y

    return None


def normalize_financial_dataframe(df: "pd.DataFrame") -> "pd.DataFrame":
    """Normalize Excel/CSV financial statements into a clean analysis-ready table."""

    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("normalize_financial_dataframe expects a pandas DataFrame")

    out = df.copy()
    out = out.dropna(axis=0, how="all").dropna(axis=1, how="all")

    if out.empty:
        return out

    scan = out.fillna("").astype(str)

    def _count_years(values) -> int:
        return sum(1 for v in values if _extract_year_number(v) is not None)

    # -------------------------------------------------------------
    # Find the BEST header row (years + descriptive text)
    # -------------------------------------------------------------
    header_row = None
    best_score = -1

    for idx in range(len(scan)):
        row = scan.iloc[idx]

        years = _count_years(row)

        if years < 2:
            continue

        text = sum(
            bool(str(v).strip()) and _extract_year_number(v) is None
            for v in row
        )

        score = years * 10 + text

        if score > best_score:
            best_score = score
            header_row = idx

    # -------------------------------------------------------------
    # Excel-style statement
    # -------------------------------------------------------------
    if header_row is not None:

        header = scan.iloc[header_row].tolist()

        new_columns = []
        seen_years = {}

        for i, value in enumerate(header):
            value = str(value).strip()

            year_val = _extract_year_number(value)

            if year_val is not None:
                year_str = str(year_val)

                if year_str in seen_years:
                    seen_years[year_str] += 1
                    year_str = f"{year_str}_{seen_years[year_str]}"
                else:
                    seen_years[year_str] = 0

                new_columns.append(year_str)

            else:
                if i == 0:
                    new_columns.append("Item")
                elif value:
                    new_columns.append(value)
                else:
                    new_columns.append(f"Column_{i}")

        out = out.iloc[header_row + 1 :].reset_index(drop=True)
        out.columns = new_columns

    # -------------------------------------------------------------
    # Original CSV logic (unchanged)
    # -------------------------------------------------------------
    else:
        columns = list(out.columns)
        renamed = {}
        drop_cols = []

        for i, col in enumerate(columns):
            col_str = str(col)
            is_unnamed = col_str.startswith("Unnamed") or col_str.strip() == ""

            if not is_unnamed:
                continue

            series = out.iloc[:, i]
            non_null = series.dropna()

            if (
                i == 0
                or (
                    len(non_null) > 0
                    and non_null.map(lambda v: isinstance(v, str)).mean() >= 0.5
                    and "Item" not in renamed.values()
                )
            ):
                if "Item" not in renamed.values():
                    renamed[col] = "Item"
                    continue

            if non_null.empty or non_null.astype(str).str.strip().eq("").all():
                drop_cols.append(col)
            else:
                renamed[col] = f"Column_{i}"

        if renamed:
            out = out.rename(columns=renamed)

        if drop_cols:
            out = out.drop(
                columns=[c for c in drop_cols if c in out.columns],
                errors="ignore",
            )

    # -------------------------------------------------------------
    # Ensure Item column exists
    # -------------------------------------------------------------
    if "Item" not in out.columns:
        out = out.rename(columns={out.columns[0]: "Item"})

    out = out.dropna(axis=1, how="all")

    # -------------------------------------------------------------
    # Remove obvious title / subtitle rows
    # -------------------------------------------------------------
    skip_patterns = [
        r"^\s*$",
        r"^\(?(?:amounts?\s+)?in\s+millions?.*$",
        r"^\(?(?:amounts?\s+)?in\s+thousands?.*$",
        r"^\(?(?:amounts?\s+)?in\s+billions?.*$",
        r"^unaudited$",
        r"^see accompanying",
        r"^the accompanying",
        r"^consolidated balance sheets?$",
        r"^consolidated statements?",
        r"^statement of financial position$",
        r"^statement of operations$",
        r"^income statement$",
        r"^cash flows?$",
        r"^statement of cash flows?$",
    ]

    keep_rows = []

    for idx, row in out.iterrows():
        label = str(row["Item"]).strip()

        if not label:
            continue

        lower = label.lower()

        if any(re.search(pattern, lower) for pattern in skip_patterns):
            continue

        if _extract_year_number(label) is not None and len(re.sub(r"\d+", "", label)) < 3:
            continue

        numeric_found = False

        for col in out.columns[1:]:
            parsed = _parse_accounting_number(row[col])

            if isinstance(parsed, (int, float)) and not pd.isna(parsed):
                numeric_found = True
                break

        if numeric_found or label:
            keep_rows.append(idx)

    out = out.loc[keep_rows].reset_index(drop=True)

    # -------------------------------------------------------------
    # Clean Item labels
    # -------------------------------------------------------------
    out["Item"] = (
        out["Item"]
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"[.\u2024\u2026]+$", "", regex=True)
        .str.strip()
    )

    # -------------------------------------------------------------
    # Convert accounting numbers
    # -------------------------------------------------------------
    for col in out.columns:
        if col == "Item":
            continue

        parsed = out[col].map(_parse_accounting_number)
        out[col] = pd.to_numeric(parsed, errors="coerce")

    out = out.dropna(axis=0, how="all")
    out = out.dropna(axis=1, how="all")

    return out.reset_index(drop=True)


def _year_columns(df: "pd.DataFrame", label_col: str = "Item") -> list:
    """Return value columns ordered by year when possible."""
    cols = [c for c in df.columns if c != label_col]
    yearish = [c for c in cols if _extract_year_number(c) is not None]
    if yearish:
        return sorted(yearish, key=lambda c: (_extract_year_number(c) or 0, str(c)))
    # Fall back to numeric columns (period headers without a 4-digit year).
    numeric = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    return numeric if numeric else cols


def _resolve_year_column(year_cols: list, year: str) -> tuple[Optional[object], Optional[str]]:
    """Match a user-supplied year string to a column name."""
    if not year:
        return None, "Error: year is required for this operation."
    needle = str(year).strip().lower()
    for col in year_cols:
        if str(col).strip().lower() == needle:
            return col, None
    year_num = _extract_year_number(needle)
    if year_num is not None:
        matches = [c for c in year_cols if _extract_year_number(c) == year_num]
        if len(matches) == 1:
            return matches[0], None
        if len(matches) > 1:
            return None, (
                f"Error: year '{year}' matches multiple columns: "
                f"{[str(c) for c in matches]}. Be more specific."
            )
    available = [str(c) for c in year_cols]
    return None, f"Error: year '{year}' not found. Available period columns: {available}."


def _find_line_rows(df: "pd.DataFrame", line_item: str, label_col: str = "Item"):
    """Locate rows whose label contains *line_item* (case-insensitive).

    Prefers a single exact label match when present so queries like
    ``"Current Assets"`` do not also hit ``"Non-current Assets"``.
    """
    if not line_item or not str(line_item).strip():
        return None, "Error: line_item is required for this operation."

    needle = str(line_item).strip()
    labels = df[label_col].astype(str)

    exact = df.loc[labels.str.strip().str.lower() == needle.lower()]
    if len(exact) == 1:
        return exact, None
    if len(exact) > 1:
        return exact, None

    mask = labels.str.contains(needle, case=False, na=False, regex=False)
    matches = df.loc[mask]
    if matches.empty:
        sample = labels.head(15).tolist()
        return None, (
            f"Error: no line item matching '{line_item}'. "
            f"Sample labels: {sample}"
        )
    return matches, None


def _fmt_amount(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _load_financial_statement(
    file_path: str,
) -> tuple[Optional["pd.DataFrame"], Optional[str], Optional[str]]:
    """Load, normalize, and detect a financial statement CSV.

    Returns ``(normalized_df, statement_type, error)``.
    """
    raw, err = load_csv(file_path)
    if err:
        return None, None, err
    if raw.empty:
        return None, None, "Error: the uploaded file has no rows."

    statement_type = detect_financial_statement(raw)
    try:
        df = normalize_financial_dataframe(raw)
    except Exception as exc:  # noqa: BLE001
        return None, statement_type, f"Error normalizing financial statement: {exc}"

    if df.empty:
        return None, statement_type, "Error: no data left after normalizing the statement."
    if "Item" not in df.columns:
        return None, statement_type, "Error: could not identify a row-label column."
    return df, statement_type, None


KNOWN_ITEMS = [
    "Total Revenue",
    "Operating Revenue",
    "Cost of Revenue",
    "Cost of Sales",
    "Net Income",
    "Net Loss",
    "Operating Income",
    "Operating Expenses",
    "Gross Profit",
    "Gross Margin",
    "Revenue",
    "EBITDA",
    "EBIT",
    "Total Assets",
    "Current Assets",
    "Non-current Assets",
    "Fixed Assets",
    "Total Liabilities",
    "Current Liabilities",
    "Non-current Liabilities",
    "Shareholders' Equity",
    "Total Equity",
    "Cash and Cash Equivalents",
    "Operating Cash Flow",
    "Free Cash Flow"
]


def infer_financial_statement_args(file_path: str, question: str) -> dict:
    """Map a free-form question to analyze_financial_statement invoke args."""
    q = (question or "").strip()
    q_lower = q.lower()
    years = re.findall(r"(?:19|20)\d{2}", q)

    args: dict = {"file_path": file_path}

    # 1. Determine Operation
    if any(
        k in q_lower
        for k in (
            "yoy",
            "year over year",
            "year-over-year",
            "growth rate",
            "% growth",
            "percent growth",
            "percentage growth",
        )
    ):
        args["operation"] = "yoy_growth"
    elif any(
        k in q_lower
        for k in (
            "compar",
            " versus ",
            " vs ",
            " vs.",
            "difference between",
            "change from",
            "changed from",
        )
    ):
        args["operation"] = "year_comparison"
    elif any(
        k in q_lower
        for k in (
            "validat",
            "tie out",
            "tie-out",
            "adds up",
            "add up",
            "sum to",
            "sum of",
            "reconcile",
            "equal the total",
            "equals the total",
            "plus",
            "+",
        )
    ) or re.search(r"\bequals?\b", q_lower):
        args["operation"] = "total_validation"
    elif years and any(
        k in q_lower
        for k in ("yearly", "by year", "for year", "in year", "value in", "value for")
    ):
        args["operation"] = "yearly_values"
    else:
        args["operation"] = "line_lookup"

    # Year assignment
    if len(years) >= 2:
        args["year_a"] = years[0]
        args["year_b"] = years[1]
        if args["operation"] == "line_lookup":
            args["operation"] = "year_comparison"
    elif len(years) == 1:
        args["year"] = years[0]
        if args["operation"] == "line_lookup":
            args["operation"] = "yearly_values"

    # 2. Extract arguments for total_validation
    if args["operation"] == "total_validation":
        sum_of = re.search(
            r"sum of\s+(.+?)(?:\s+(?:equal|equals|match(?:es)?|to)\b|$)",
            q,
            flags=re.IGNORECASE,
        )
        plus_parts = re.search(
            r"(.+?)\s*=\s*(.+)$",
            q,
        )
        plus_natural = re.search(
            r"(?:does|do)?\s*(.+?)(?:\s*\+\s*|\s+plus\s+)(.+?)\s+(?:equal|equals|are|is|to)\s+(.+)$",
            q,
            flags=re.IGNORECASE
        )

        if sum_of:
            args["component_lines"] = sum_of.group(1).strip(" .,;:?")
            total_m = re.search(
                r"(?:equal|equals|match(?:es)?|to)\s+(.+)$",
                q,
                flags=re.IGNORECASE,
            )
            if total_m:
                args["total_line"] = total_m.group(1).strip(" .,;:?")
        
        elif plus_natural:
            left, right, total_part = plus_natural.groups()
            args["component_lines"] = f"{left.strip()}, {right.strip()}"
            
            tot = total_part.strip(" ?.,;:\"'")
            for y in years:
                tot = re.sub(rf"\b(?:in\s+)?{y}\b", "", tot, flags=re.IGNORECASE).strip()
            args["total_line"] = tot

        elif plus_parts and ("+" in plus_parts.group(1) or "+" in plus_parts.group(2)):
            left, right = plus_parts.group(1).strip(), plus_parts.group(2).strip()
            if "+" in left:
                args["component_lines"] = left.replace("+", ",")
                args["total_line"] = right
            else:
                args["component_lines"] = right.replace("+", ",")
                args["total_line"] = left

    # 3. Derive a line_item label
    found_item = None
    for item in sorted(KNOWN_ITEMS, key=len, reverse=True):
        if item.lower() in q_lower:
            found_item = item
            break

    if found_item and args["operation"] != "total_validation":
        args["line_item"] = found_item
    elif found_item and "total_line" not in args:
        args["line_item"] = found_item
    else:
        line_item = q
        for y in years:
            line_item = re.sub(rf"\b{y}\b", " ", line_item)
        
        fluff = [
            r"\byoy\b", r"\byear[- ]over[- ]year\b", r"\bgrowth(?:\s+rate)?\b",
            r"\bpercent(?:age)?\s+growth\b", r"\bcompar(?:e|ison|ing)?\b", r"\bversus\b",
            r"\bvs\.?\b", r"\bdifference between\b", r"\bchange(?:d)? from\b",
            r"\bvalidat(?:e|ion|ing)?\b", r"\btie[- ]?out\b", r"\breconcile\b",
            r"\byearly values?\b", r"\bby year\b", r"\bfor year\b", r"\bin year\b",
            r"\bvalue(?:s)? (?:in|for|of)\b", r"\bwhat (?:is|was|are|were)\b",
            r"\bshow(?: me)?\b", r"\bfind\b", r"\blook ?up\b", r"\bget\b", r"\bthe\b",
            r"\bplease\b", r"\bhow much\b", r"\bfrom\b", r"\bto\b", r"\bin\b", r"\bfor\b",
            r"\bbetween\b", r"\bdoes\b", r"\bdo\b"
        ]
        
        for pattern in fluff:
            line_item = re.sub(pattern, " ", line_item, flags=re.IGNORECASE)
            
        line_item = " ".join(line_item.split()).strip(" ?.,:;\"'`")
        
        if line_item and args["operation"] != "total_validation":
            args["line_item"] = line_item
        elif line_item and "total_line" not in args:
            args["line_item"] = line_item

    return args


@tool
def analyze_financial_statement(
    file_path: str,
    operation: str,
    line_item: Optional[str] = None,
    year: Optional[str] = None,
    year_a: Optional[str] = None,
    year_b: Optional[str] = None,
    total_line: Optional[str] = None,
    component_lines: Optional[str] = None,
) -> str:
    """Analyze an uploaded Balance Sheet, Income Statement, or Cash Flow CSV.

    Prefer this over get_csv_agent / csv_row_sum for ANY financial-statement questions 
    about specific line items (e.g., "Net Income", "EBITDA", "EBIT", "Gross Profit", "Revenue", "Total Assets"), 
    period values, year comparisons, YoY growth, or checking whether a total equals the sum of its components.

    Args:
        file_path: path to the uploaded CSV (same path used by other CSV tools).
        operation: one of:
            - line_lookup: find a line item and return its values across periods
            - yearly_values: return period values for a line (optionally one year)
            - year_comparison: compare year_a vs year_b for a line item
            - yoy_growth: year-over-year growth for a line item
            - total_validation: check that total_line ≈ sum(component_lines)
        line_item: row label to look up (required for lookup/yearly/compare/yoy).
        year: optional single period for yearly_values or total_validation.
        year_a: earlier/base period for comparison or YoY (optional; defaults to
            the second-latest year column).
        year_b: later/comparison period (optional; defaults to the latest year).
        total_line: expected total row label for total_validation.
        component_lines: comma-separated component row labels to sum for
            total_validation (e.g. "Cash, Receivables, Inventory").
    """
    df, statement_type, err = _load_financial_statement(file_path)
    if err:
        return err

    label_col = "Item"
    year_cols = _year_columns(df, label_col)
    if not year_cols:
        return "Error: no period/year value columns found after normalization."

    detected = statement_type or "Unknown"
    header = f"Statement type: {detected}\nPeriod columns: {[str(c) for c in year_cols]}\n"

    op = operation.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "lookup": "line_lookup",
        "line": "line_lookup",
        "yearly": "yearly_values",
        "values": "yearly_values",
        "compare": "year_comparison",
        "comparison": "year_comparison",
        "yoy": "yoy_growth",
        "growth": "yoy_growth",
        "validate": "total_validation",
        "validation": "total_validation",
        "total": "total_validation",
    }
    op = aliases.get(op, op)

    try:
        if op == "line_lookup":
            matches, find_err = _find_line_rows(df, line_item or "", label_col)
            if find_err:
                return find_err
            if len(matches) > 1:
                labels = matches[label_col].astype(str).tolist()
                return (
                    f"Found {len(matches)} lines matching '{line_item}': {labels}. "
                    f"Be more specific."
                )
            row = matches.iloc[0]
            parts = [f"{c}={_fmt_amount(row[c])}" for c in year_cols]
            return (
                header
                + f"Line lookup: '{row[label_col]}'\n"
                + ", ".join(parts)
            )

        if op == "yearly_values":
            matches, find_err = _find_line_rows(df, line_item or "", label_col)
            if find_err:
                return find_err
            if len(matches) > 1:
                labels = matches[label_col].astype(str).tolist()
                return (
                    f"Found {len(matches)} lines matching '{line_item}': {labels}. "
                    f"Be more specific."
                )
            row = matches.iloc[0]
            if year:
                col, col_err = _resolve_year_column(year_cols, year)
                if col_err:
                    return col_err
                return (
                    header
                    + f"Yearly value for '{row[label_col]}' in {col}: "
                    + _fmt_amount(row[col])
                )
            parts = [f"{c}={_fmt_amount(row[c])}" for c in year_cols]
            return (
                header
                + f"Yearly values for '{row[label_col]}':\n"
                + ", ".join(parts)
            )

        if op in {"year_comparison", "yoy_growth"}:
            matches, find_err = _find_line_rows(df, line_item or "", label_col)
            if find_err:
                return find_err
            if len(matches) > 1:
                labels = matches[label_col].astype(str).tolist()
                return (
                    f"Found {len(matches)} lines matching '{line_item}': {labels}. "
                    f"Be more specific."
                )
            row = matches.iloc[0]

            if year_a and year_b:
                col_a, err_a = _resolve_year_column(year_cols, year_a)
                if err_a:
                    return err_a
                col_b, err_b = _resolve_year_column(year_cols, year_b)
                if err_b:
                    return err_b
            elif len(year_cols) >= 2:
                col_a, col_b = year_cols[-2], year_cols[-1]
            else:
                return (
                    "Error: need at least two period columns (or year_a and year_b) "
                    "for comparison / YoY growth."
                )

            val_a = pd.to_numeric(row[col_a], errors="coerce")
            val_b = pd.to_numeric(row[col_b], errors="coerce")
            if pd.isna(val_a) or pd.isna(val_b):
                return (
                    header
                    + f"Error: missing numeric values for '{row[label_col]}' "
                    + f"({col_a}={_fmt_amount(row[col_a])}, "
                    + f"{col_b}={_fmt_amount(row[col_b])})."
                )

            delta = float(val_b) - float(val_a)
            if op == "year_comparison":
                return (
                    header
                    + f"Year comparison for '{row[label_col]}':\n"
                    + f"{col_a} = {_fmt_amount(val_a)}\n"
                    + f"{col_b} = {_fmt_amount(val_b)}\n"
                    + f"Change ({col_b} - {col_a}) = {_fmt_amount(delta)}"
                )

            if float(val_a) == 0:
                return (
                    header
                    + f"YoY growth for '{row[label_col]}':\n"
                    + f"{col_a} = {_fmt_amount(val_a)}, {col_b} = {_fmt_amount(val_b)}\n"
                    + "Cannot compute YoY growth: base year value is zero."
                )
            growth = delta / abs(float(val_a))
            return (
                header
                + f"YoY growth for '{row[label_col]}':\n"
                + f"{col_a} = {_fmt_amount(val_a)}\n"
                + f"{col_b} = {_fmt_amount(val_b)}\n"
                + f"Change = {_fmt_amount(delta)}\n"
                + f"YoY growth = {growth:.2%}"
            )

        if op == "total_validation":
            if not total_line or not str(total_line).strip():
                return "Error: total_line is required for total_validation."
            if not component_lines or not str(component_lines).strip():
                return (
                    "Error: component_lines is required for total_validation "
                    "(comma-separated labels to sum)."
                )

            total_matches, total_err = _find_line_rows(df, total_line, label_col)
            if total_err:
                return total_err.replace("line item", "total line")
            if len(total_matches) > 1:
                labels = total_matches[label_col].astype(str).tolist()
                return (
                    f"Found {len(total_matches)} totals matching '{total_line}': "
                    f"{labels}. Be more specific."
                )
            total_row = total_matches.iloc[0]

            components = [p.strip() for p in str(component_lines).split(",") if p.strip()]
            if not components:
                return "Error: component_lines produced no labels after splitting."

            component_rows = []
            for label in components:
                matches, find_err = _find_line_rows(df, label, label_col)
                if find_err:
                    return find_err
                if len(matches) > 1:
                    labels = matches[label_col].astype(str).tolist()
                    return (
                        f"Found {len(matches)} lines matching component '{label}': "
                        f"{labels}. Be more specific."
                    )
                component_rows.append(matches.iloc[0])

            cols_to_check = year_cols
            if year:
                col, col_err = _resolve_year_column(year_cols, year)
                if col_err:
                    return col_err
                cols_to_check = [col]

            lines_out = [
                header
                + f"Total validation: '{total_row[label_col]}' vs sum of "
                + f"{[r[label_col] for r in component_rows]}"
            ]
            
            abs_tol = 0.01
            rel_tol = 0.001

            for col in cols_to_check:
                expected = pd.to_numeric(total_row[col], errors="coerce")
                parts = []
                part_sum = 0.0
                missing = False
                for crow in component_rows:
                    raw_val = pd.to_numeric(crow[col], errors="coerce")
                    if pd.isna(raw_val):
                        missing = True
                        parts.append(f"{crow[label_col]}=n/a")
                    else:
                        part_sum += float(raw_val)
                        parts.append(f"{crow[label_col]}={_fmt_amount(raw_val)}")

                if missing or pd.isna(expected):
                    lines_out.append(
                        f"{col}: incomplete data "
                        f"(total={_fmt_amount(expected)}; components: {', '.join(parts)})"
                    )
                    continue

                expected_f = float(expected)
                diff = part_sum - expected_f
                ok = abs(diff) <= max(abs_tol, rel_tol * abs(expected_f))
                status = "PASS" if ok else "FAIL"
                lines_out.append(
                    f"{col}: {status} - sum(components)={_fmt_amount(part_sum)}, "
                    f"total={_fmt_amount(expected_f)}, diff={_fmt_amount(diff)} "
                    f"[{'; '.join(parts)}]"
                )

            return "\n".join(lines_out)

        return (
            f"Error: unsupported operation '{operation}'. "
            "Use one of: line_lookup, yearly_values, year_comparison, "
            "yoy_growth, total_validation."
        )
    except Exception as exc:  # noqa: BLE001
        return f"Error analyzing financial statement: {exc}"


# Backward-compatible private alias (old call sites used the underscore name).
_infer_financial_statement_args = infer_financial_statement_args
