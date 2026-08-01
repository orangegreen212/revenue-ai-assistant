"""Reproduce csv-chat tool loop. Run:

    set PYTHONPATH=.
    python scripts/debug_tool_calling.py
"""

from __future__ import annotations

import os
import tempfile

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from rag.rag_core import CHAT_TOOLS, get_llm, run_chat_with_tools  # noqa: E402


def main() -> None:
    df = pd.DataFrame(
        {
            "Unnamed: 0": [
                "Balance Sheet",
                "Cash",
                "Current Assets",
                "Non-current Assets",
                "Total Assets",
                "Total Liabilities",
                "Shareholders Equity",
            ],
            "2024": ["", "1000", "3500", "1500", "5000", "3000", "2000"],
            "2025": ["", "1200", "3700", "1800", "5500", "3200", "2300"],
        }
    )
    path = tempfile.mktemp(suffix=".csv")
    df.to_csv(path, index=False)

    cols = ", ".join(df.columns.astype(str))
    context = (
        "CSV uploaded.\n\n"
        f"Real file path:\n{path}\n\n"
        f"Columns:\n{cols}\n\n"
        f"Rows:\n{len(df)}\n\n"
        "When using get_csv_agent, csv_aggregate, csv_row_sum, or "
        "analyze_financial_statement, use the exact file path above.\n"
    )

    llm = get_llm()
    print("OPENROUTER_MODEL=", os.getenv("OPENROUTER_MODEL"))
    print("registered tools:", [t.name for t in CHAT_TOOLS])

    for q in ["What are Total Assets in 2025?", "What are Current Assets?"]:
        print("\n========== QUERY:", q, "==========")
        answer, tools_used = run_chat_with_tools(
            llm, context, q, allow_any_csv_topic=True, lang="en"
        )
        print("TOOLS_USED:", tools_used)
        print("ANSWER:", answer[:800])

    os.remove(path)


if __name__ == "__main__":
    main()
