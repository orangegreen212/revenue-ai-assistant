"""CSV-facing LangChain tools: exact pandas aggregates, row sums, and a
free-form pandas-agent fallback for uploaded CSV/Excel files."""

from typing import Optional

import pandas as pd
from langchain_core.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from tools.csv_io import load_csv as _load_csv
from tools.financial_statement import (
    analyze_financial_statement,
    detect_financial_statement,
    infer_financial_statement_args,
)


@tool
def csv_aggregate(
    file_path: str,
    column: str,
    operation: str,
    groupby: Optional[str] = None,
) -> str:
    """Compute an exact numeric aggregate over a CSV column using pandas (no LLM reasoning involved).

    Use this instead of get_csv_agent whenever the question is a straightforward
    total/average/count/min/max, optionally grouped by another column — it returns
    the real computed number, not a guess.

    Args:
        file_path: path to the CSV (same path passed to get_csv_agent).
        column: the numeric column to aggregate, e.g. "session_time".
        operation: one of "sum", "mean", "count", "min", "max", "median".
        groupby: optional column to group by, e.g. "country".
    """
    df, err = _load_csv(file_path)
    if err:
        return err

    if column not in df.columns:
        return f"Error: column '{column}' not found. Available columns: {list(df.columns)}."

    op = operation.strip().lower()
    valid_ops = {"sum", "mean", "count", "min", "max", "median"}
    if op not in valid_ops:
        return f"Error: unsupported operation '{operation}'. Use one of: {sorted(valid_ops)}."

    try:
        if groupby:
            if groupby not in df.columns:
                return f"Error: groupby column '{groupby}' not found. Available columns: {list(df.columns)}."
            result = df.groupby(groupby)[column].agg(op)
            return f"{op}({column}) grouped by {groupby}:\n" + result.to_string()
        else:
            result = df[column].agg(op)
            return f"{op}({column}) over {len(df)} rows = {result}"
    except Exception as exc:  # noqa: BLE001
        return f"Error computing {op} on '{column}': {exc}"


@tool
def csv_row_sum(file_path: str, label: str, label_column: Optional[str] = None) -> str:
    """Sum a row's values across all numeric columns — resilient to financial CSV formats."""
    df, err = _load_csv(file_path)
    if err:
        return err

    if df.empty:
        return "Error: the uploaded CSV has no rows."

    label_col = label_column or df.columns[0]
    if label_col not in df.columns:
        return f"Error: label column '{label_col}' not found. Available columns: {list(df.columns)}."

    mask = df[label_col].astype(str).str.contains(label, case=False, na=False, regex=False)
    matches = df[mask]

    if matches.empty:
        return (
            f"Error: no row found where '{label_col}' contains '{label}'. "
            f"Sample values in that column: {df[label_col].astype(str).head(10).tolist()}"
        )
    if len(matches) > 1:
        row_labels = matches[label_col].astype(str).tolist()
        return (
            f"Found {len(matches)} rows matching '{label}': {row_labels}. "
            f"Be more specific, or call this again with the exact label."
        )

    row = matches.iloc[0]
    total = 0.0
    breakdown = []

    # Aggressively clean and extract numbers from the matched row
    for c in df.columns:
        if c == label_col:
            continue
        
        # Convert to string, strip spaces, commas, and dollar signs
        raw_val = str(row[c]).strip().replace(',', '').replace('$', '')
        
        # Handle accounting negative format: "(100.50)" -> "-100.50"
        if raw_val.startswith('(') and raw_val.endswith(')'):
            raw_val = '-' + raw_val[1:-1]
            
        try:
            val = float(raw_val)
            if pd.notna(val):
                total += val
                breakdown.append(f"{c}={val}")
        except ValueError:
            # Skip cells that are truly text (like "null", "September 27", etc.)
            continue

    if not breakdown:
        return f"Error: no numeric values found to sum for row '{label}'."

    breakdown_str = ", ".join(breakdown)
    return f"Row '{row[label_col]}': sum across {len(breakdown)} columns = {total}\nBreakdown: {breakdown_str}"


@tool
def get_csv_agent(file_path: str, question: str) -> str:
    """Analyze an uploaded CSV with free-form reasoning for questions that a simple
    aggregate can't answer (e.g. filtering, multi-step logic, comparisons).

    For plain totals/averages/counts, prefer csv_aggregate — it computes the exact
    number directly instead of relying on the model's own arithmetic.
    """
    df, err = _load_csv(file_path)
    if err:
        return err

    if df.empty:
        return "Error: the uploaded CSV has no rows."

    from rag.rag_core import has_prompt_injection

    sample_text = " ".join(
        str(v) for v in df.head(50).astype(str).values.flatten()
    )
    if has_prompt_injection(sample_text):
        return (
            "Error: the uploaded file contains text patterns that look like "
            "prompt-injection attempts and was not passed to the code-executing "
            "agent. Try csv_aggregate instead, or clean the file and re-upload."
        )

    if detect_financial_statement(df) is not None:
        return analyze_financial_statement.invoke(
            infer_financial_statement_args(file_path, question)
        )

    from rag.rag_core import get_llm
    llm = get_llm()

    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        allow_dangerous_code=True,
        handle_parsing_errors=True,
    )

    try:
        result = agent.invoke({"input": question})
        return str(result.get("output", result))
    except Exception as exc:  # noqa: BLE001
        return f"Error analyzing CSV: {exc}"
