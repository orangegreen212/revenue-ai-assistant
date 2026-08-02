"""Analytics helpers and LangChain tools for the Revenue AI Assistant."""

import os
import re
from typing import Optional

import pandas as pd
from langchain_core.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


def _load_csv(file_path: str) -> tuple[Optional["pd.DataFrame"], Optional[str]]:
    """Shared file-loading boilerplate for csv_aggregate and get_csv_agent.
    Returns (dataframe, None) on success or (None, error_message) on failure.
    """
    if not os.path.exists(file_path):
        return None, f"Error: file not found at '{file_path}'."
    try:
        return pd.read_csv(file_path), None
    except Exception as exc:  # noqa: BLE001
        return None, f"Error reading CSV at '{file_path}': {exc}"


# Rough SaaS industry reference ranges (illustrative, not audited benchmarks).
_KPI_BENCHMARKS = {
    "en": {
        "mrr": {
            "description": "Monthly Recurring Revenue growth and stability",
            "good": "Steady MoM growth with clear New/Expansion/Churn bridge",
            "typical": "Early-stage: high MoM % growth; mature: lower % but larger $",
            "watchout": "Growth funded only by discounts or one-time fees",
        },
        "arr": {
            "description": "Annual Recurring Revenue scale",
            "good": "Consistent YoY ARR growth with healthy net new ARR",
            "typical": "Varies widely by stage; investors focus on growth rate + retention",
            "watchout": "Counting non-recurring revenue as ARR",
        },
        "nrr": {
            "description": "Net Revenue Retention",
            "good": "≥ 110% (strong); 120%+ excellent for B2B SaaS",
            "typical": "100–120% for healthy B2B; SMB often closer to ~100%",
            "watchout": "NRR inflated by a few large expansions while GRR is weak",
        },
        "grr": {
            "description": "Gross Revenue Retention",
            "good": "≥ 90% annually (context-dependent)",
            "typical": "85–95% for solid B2B SaaS",
            "watchout": "Reporting GRR > 100% (expansion must be excluded)",
        },
        "churn": {
            "description": "Logo or revenue churn rate",
            "good": "Monthly logo churn often < 2–3% (SMB higher; enterprise lower)",
            "typical": "SMB monthly ~3–7%; enterprise annual logo churn often mid-single digits",
            "watchout": "Mixing logo churn with revenue churn without labeling",
        },
        "cac": {
            "description": "Customer Acquisition Cost",
            "good": "Sustainable vs LTV; often judged via LTV:CAC and payback",
            "typical": "Highly channel- and segment-dependent",
            "watchout": "Excluding sales salaries/commissions from fully loaded CAC",
        },
        "ltv": {
            "description": "Customer Lifetime Value",
            "good": "LTV:CAC around 3:1 or higher (rule of thumb)",
            "typical": "Depends on margin, churn, and ARPU assumptions",
            "watchout": "Using revenue LTV instead of gross-profit LTV in ratios",
        },
        "payback": {
            "description": "CAC payback period (months)",
            "good": "Often < 12 months target (tighter for SMB/PLG)",
            "typical": "6–18 months depending on motion (PLG vs enterprise)",
            "watchout": "Using revenue instead of gross profit in the denominator",
        },
        "arpu": {
            "description": "Average Revenue Per User/Account",
            "good": "Rising ARPU from pricing, mix, or expansion without hurting retention",
            "typical": "Wide range by ICP and packaging",
            "watchout": "Mixing seats vs accounts in the denominator",
        },
    },
    "uk": {
        "mrr": {
            "description": "Зростання та стабільність щомісячного повторюваного доходу",
            "good": "Стабільне MoM-зростання з чітким New/Expansion/Churn bridge",
            "typical": "На старті: високий % MoM-зростання; у зрілих компаніях: нижчий %, але більша сума",
            "watchout": "Зростання, яке тримається лише на знижках чи разових платежах",
        },
        "arr": {
            "description": "Масштаб річного повторюваного доходу",
            "good": "Стабільне YoY-зростання ARR зі здоровим net new ARR",
            "typical": "Сильно залежить від стадії; інвестори дивляться на темп зростання + утримання",
            "watchout": "Врахування неповторюваної виручки як ARR",
        },
        "nrr": {
            "description": "Чисте утримання виручки (NRR)",
            "good": "≥ 110% (сильно); 120%+ відмінно для B2B SaaS",
            "typical": "100–120% для здорового B2B; SMB часто ближче до ~100%",
            "watchout": "NRR завищений кількома великими expansion при слабкому GRR",
        },
        "grr": {
            "description": "Валове утримання виручки (GRR)",
            "good": "≥ 90% на рік (залежно від контексту)",
            "typical": "85–95% для здорового B2B SaaS",
            "watchout": "GRR понад 100% (expansion має бути виключений)",
        },
        "churn": {
            "description": "Відтік клієнтів або виручки",
            "good": "Місячний logo churn часто < 2–3% (для SMB вищий, для enterprise нижчий)",
            "typical": "SMB ~3–7% на місяць; enterprise річний logo churn часто одноцифровий",
            "watchout": "Змішування logo churn і revenue churn без позначення",
        },
        "cac": {
            "description": "Вартість залучення клієнта",
            "good": "Стійка відносно LTV; оцінюється через LTV:CAC і payback",
            "typical": "Сильно залежить від каналу й сегмента",
            "watchout": "Виключення зарплат/комісій продажів з fully loaded CAC",
        },
        "ltv": {
            "description": "Довічна цінність клієнта",
            "good": "LTV:CAC близько 3:1 або вище (емпіричне правило)",
            "typical": "Залежить від маржі, churn та ARPU",
            "watchout": "Використання revenue LTV замість gross-profit LTV у співвідношеннях",
        },
        "payback": {
            "description": "Термін окупності CAC (місяців)",
            "good": "Часто ціль < 12 місяців (жорсткіше для SMB/PLG)",
            "typical": "6–18 місяців залежно від моделі продажів (PLG vs enterprise)",
            "watchout": "Використання виручки замість валового прибутку в знаменнику",
        },
        "arpu": {
            "description": "Середній дохід на користувача/акаунт",
            "good": "Зростання ARPU від ціноутворення, міксу чи expansion без шкоди утриманню",
            "typical": "Широкий діапазон залежно від ICP і пакування",
            "watchout": "Змішування місць (seats) та акаунтів у знаменнику",
        },
    },
}


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

    # Defense in depth: has_prompt_injection() already guards the user's typed
    # question, but the CSV's own cell values are also fed to an LLM that can
    # execute code (allow_dangerous_code=True below). Scan cell text for the
    # same injection markers so a malicious *file* can't smuggle instructions
    # in through the data instead of the chat box.
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

    # Financial statements are handled by the dedicated analyzer (line lookup,
    # yearly values, comparisons, YoY, total validation) instead of the
    # code-executing pandas agent below.
    if detect_financial_statement(df) is not None:
        return analyze_financial_statement.invoke(
            _infer_financial_statement_args(file_path, question)
        )

    # Lazy import to avoid a circular import (rag_core imports this module's
    # tools) — reuses the same LLM config as the main chat flow instead of
    # duplicating ChatOpenAI instantiation with different parameters here.
    from rag.rag_core import get_llm

    llm = get_llm()

    # SECURITY NOTE: allow_dangerous_code=True lets the agent execute LLM-generated
    # Python via pandas' eval/exec internally. This is a known, named trade-off in
    # LangChain (hence the flag's name) — acceptable for a course project running
    # in an isolated container with no persistent secrets in the runtime, but NOT
    # something to enable as-is against untrusted multi-tenant production traffic
    # without a real sandboxed execution environment (e.g. gVisor, a locked-down
    # subprocess, or a separate worker with no filesystem/network access).
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
    except Exception as exc:  # noqa: BLE001 — surface the error to the caller
        return f"Error analyzing CSV: {exc}"


@tool
def calculate_kpi(
    kpi_name: str,
    value_a: float,
    value_b: float,
    value_c: Optional[float] = None,
    lang: str = "en",
) -> str:
    """Calculate a common SaaS KPI from simple numeric inputs.

    Supported kpi_name values (case-insensitive):
    - mrr: value_a = sum of monthly recurring fees
    - arr: value_a = MRR (returns ARR = MRR * 12)
    - cac: value_a = sales & marketing cost, value_b = new customers
    - ltv: value_a = ARPU, value_b = monthly churn rate (0-1),
            value_c = gross margin % (0-1, default 0.8)
    - churn: value_a = lost customers or churned MRR,
             value_b = starting customers or starting MRR
    - nrr: value_a = ending ARR of starting cohort,
           value_b = beginning ARR of starting cohort
    - grr: value_a = retained ARR before expansion,
           value_b = beginning ARR
    - payback: value_a = CAC, value_b = ARPU,
               value_c = gross margin % (0-1, default 0.8)
    - arpu: value_a = total MRR, value_b = active customers
    - ltv_cac: value_a = LTV, value_b = CAC
    - lang: "en" or "uk" — language of the returned explanation text.
    """
    name = kpi_name.strip().lower().replace(" ", "_").replace("-", "_")
    uk = lang == "uk"

    try:
        if name == "mrr":
            result = value_a
            detail = f"MRR = {result:,.2f}"

        elif name == "arr":
            result = value_a * 12
            detail = (
                f"ARR = MRR × 12 = {value_a:,.2f} × 12 = {result:,.2f}"
            )

        elif name == "cac":
            if value_b == 0:
                return ("Помилка: кількість нових клієнтів (value_b) не може бути нулем."
                        if uk else "Error: new customers (value_b) cannot be zero.")
            result = value_a / value_b
            detail = (
                f"CAC = Витрати на продажі й маркетинг / нові клієнти = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:,.2f}"
                if uk else
                f"CAC = S&M cost / new customers = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:,.2f}"
            )

        elif name == "ltv":
            churn = value_b
            margin = 0.8 if value_c is None else value_c
            if churn <= 0:
                return ("Помилка: churn rate (value_b) має бути > 0."
                        if uk else "Error: churn rate (value_b) must be > 0.")
            result = (value_a * margin) / churn
            detail = (
                f"LTV = ARPU × маржа / churn = "
                f"{value_a:,.2f} × {margin:.2%} / {churn:.2%} = {result:,.2f}"
                if uk else
                f"LTV = ARPU × margin / churn = "
                f"{value_a:,.2f} × {margin:.2%} / {churn:.2%} = {result:,.2f}"
            )

        elif name == "churn":
            if value_b == 0:
                return ("Помилка: початкова база (value_b) не може бути нулем."
                        if uk else "Error: starting base (value_b) cannot be zero.")
            result = value_a / value_b
            detail = (
                f"Churn rate = втрачено / на старт = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:.2%}"
                if uk else
                f"Churn rate = lost / starting = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:.2%}"
            )

        elif name == "nrr":
            if value_b == 0:
                return ("Помилка: початковий ARR (value_b) не може бути нулем."
                        if uk else "Error: beginning ARR (value_b) cannot be zero.")
            result = value_a / value_b
            detail = (
                f"NRR = кінцевий ARR когорти / початковий ARR = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:.2%}"
                if uk else
                f"NRR = ending cohort ARR / beginning ARR = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:.2%}"
            )

        elif name == "grr":
            if value_b == 0:
                return ("Помилка: початковий ARR (value_b) не може бути нулем."
                        if uk else "Error: beginning ARR (value_b) cannot be zero.")
            result = min(value_a / value_b, 1.0)
            detail = (
                f"GRR = утриманий ARR / початковий ARR = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:.2%} (обмежено 100%)"
                if uk else
                f"GRR = retained ARR / beginning ARR = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:.2%} "
                f"(capped at 100%)"
            )

        elif name in {"payback", "payback_period", "cac_payback"}:
            margin = 0.8 if value_c is None else value_c
            monthly_gp = value_b * margin
            if monthly_gp <= 0:
                return ("Помилка: ARPU × маржа має бути > 0."
                        if uk else "Error: ARPU × margin must be > 0.")
            result = value_a / monthly_gp
            detail = (
                f"Payback (місяців) = CAC / (ARPU × маржа) = "
                f"{value_a:,.2f} / ({value_b:,.2f} × {margin:.2%}) = "
                f"{result:.2f} міс."
                if uk else
                f"Payback (months) = CAC / (ARPU × margin) = "
                f"{value_a:,.2f} / ({value_b:,.2f} × {margin:.2%}) = "
                f"{result:.2f} months"
            )

        elif name == "arpu":
            if value_b == 0:
                return ("Помилка: активні клієнти (value_b) не можуть бути нулем."
                        if uk else "Error: active customers (value_b) cannot be zero.")
            result = value_a / value_b
            detail = (
                f"ARPU = загальний MRR / клієнти = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:,.2f}"
                if uk else
                f"ARPU = total MRR / customers = "
                f"{value_a:,.2f} / {value_b:,.2f} = {result:,.2f}"
            )

        elif name in {"ltv_cac", "ltv:cac", "ltvtocac"}:
            if value_b == 0:
                return ("Помилка: CAC (value_b) не може бути нулем."
                        if uk else "Error: CAC (value_b) cannot be zero.")
            result = value_a / value_b
            detail = (
                f"LTV:CAC = {value_a:,.2f} / {value_b:,.2f} = {result:.2f}:1"
            )

        else:
            supported = (
                "mrr, arr, cac, ltv, churn, nrr, grr, payback, arpu, ltv_cac"
            )
            if uk:
                return f"Непідтримувана метрика '{kpi_name}'. Доступні: {supported}."
            return f"Unsupported kpi_name '{kpi_name}'. Supported: {supported}."

        return detail
    except Exception as exc:  # noqa: BLE001 — tool should return errors to the agent
        if uk:
            return f"Помилка розрахунку KPI '{kpi_name}': {exc}"
        return f"Error calculating KPI '{kpi_name}': {exc}"


@tool
def generate_sql(metric_or_question: str, table_hint: str = "subscriptions") -> str:
    """Generate a simple illustrative SQL snippet for a SaaS metric or analytics question.

    Args:
        metric_or_question: Metric name (e.g. MRR, churn) or a short question.
        table_hint: Primary table name to use in the SQL (default: subscriptions).
    """
    q = metric_or_question.strip().lower()
    table = table_hint.strip() or "subscriptions"

    if "nrr" in q or "net revenue retention" in q or "net dollar" in q:
        return f"""-- Net Revenue Retention (illustrative cohort SQL)
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-02-01'
    GROUP BY customer_id
)
SELECT
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) AS nrr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;"""

    if "grr" in q or "gross revenue retention" in q or "gross dollar" in q:
        return f"""-- Gross Revenue Retention (expansion excluded / capped)
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-02-01'
    GROUP BY customer_id
)
SELECT
    SUM(LEAST(COALESCE(e.end_mrr, 0), b.begin_mrr))
        / NULLIF(SUM(b.begin_mrr), 0) AS grr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;"""

    if "churn" in q:
        return f"""-- Logo and revenue churn for one month
WITH start_customers AS (
    SELECT customer_id, mrr AS start_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
),
churned AS (
    SELECT s.customer_id, s.start_mrr
    FROM start_customers s
    LEFT JOIN mrr_snapshots e
      ON s.customer_id = e.customer_id
     AND e.snapshot_date = DATE '2026-02-01'
    WHERE e.customer_id IS NULL OR e.mrr = 0
)
SELECT
    (SELECT COUNT(*) FROM churned) * 1.0
        / NULLIF((SELECT COUNT(*) FROM start_customers), 0) AS logo_churn_rate,
    (SELECT SUM(start_mrr) FROM churned) * 1.0
        / NULLIF((SELECT SUM(start_mrr) FROM start_customers), 0) AS revenue_churn_rate;"""

    if "cac" in q or "acquisition" in q:
        return f"""-- Blended CAC by month
SELECT
    DATE_TRUNC('month', c.first_paid_date) AS cohort_month,
    SUM(s.amount) / NULLIF(COUNT(DISTINCT c.customer_id), 0) AS cac
FROM customers c
JOIN sales_marketing_costs s
  ON DATE_TRUNC('month', s.spend_date) = DATE_TRUNC('month', c.first_paid_date)
GROUP BY 1
ORDER BY 1;"""

    if "ltv" in q or "lifetime" in q:
        return f"""-- Approximate LTV by plan (ARPU * margin / monthly churn)
SELECT
    plan_name,
    AVG(mrr) AS arpu,
    (AVG(mrr) * 0.80) / NULLIF(AVG(monthly_churn_rate), 0) AS ltv_est
FROM {table}
GROUP BY plan_name;"""

    if "arpu" in q:
        return f"""-- ARPU by plan
SELECT
    plan_name,
    SUM(mrr) / NULLIF(COUNT(DISTINCT customer_id), 0) AS arpu
FROM {table}
WHERE status = 'active'
GROUP BY plan_name;"""

    if "arr" in q:
        return f"""-- ARR snapshot from active subscriptions
SELECT
    SUM(
        CASE billing_interval
            WHEN 'month' THEN amount * 12
            WHEN 'quarter' THEN amount * 4
            WHEN 'year' THEN amount
            ELSE NULL
        END
    ) AS total_arr
FROM {table}
WHERE status = 'active';"""

    if "payback" in q:
        return f"""-- CAC payback months by cohort (assumes 80% gross margin)
SELECT
    cohort_month,
    cac / NULLIF(avg_starting_mrr * 0.80, 0) AS payback_months
FROM cohort_unit_economics
ORDER BY cohort_month;"""

    # Default: MRR-style query
    return f"""-- MRR by customer (normalize billing intervals to monthly)
SELECT
    customer_id,
    SUM(
        CASE billing_interval
            WHEN 'month' THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year' THEN amount / 12.0
            ELSE NULL
        END
    ) AS customer_mrr
FROM {table}
WHERE status = 'active'
GROUP BY customer_id
ORDER BY customer_mrr DESC;
-- Tip: rephrase with a metric name (MRR, ARR, NRR, churn, CAC, LTV, ARPU, payback)
-- for a more targeted template. Question was: {metric_or_question}"""


@tool
def get_benchmark(metric_name: str, lang: str = "en") -> str:
    """Return simple SaaS benchmark guidance for a revenue metric.

    Args:
        metric_name: One of mrr, arr, nrr, grr, churn, cac, ltv, payback, arpu.
        lang: "en" or "uk" — language of the returned text.
    """
    key = metric_name.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "net_revenue_retention": "nrr",
        "net_dollar_retention": "nrr",
        "gross_revenue_retention": "grr",
        "gross_dollar_retention": "grr",
        "payback_period": "payback",
        "cac_payback": "payback",
        "customer_acquisition_cost": "cac",
        "lifetime_value": "ltv",
        "clv": "ltv",
    }
    key = aliases.get(key, key)
    lang = lang if lang in _KPI_BENCHMARKS else "en"
    bench_table = _KPI_BENCHMARKS[lang]

    data = bench_table.get(key)
    if not data:
        supported = ", ".join(sorted(bench_table))
        if lang == "uk":
            return f"Бенчмарк для '{metric_name}' не знайдено. Спробуй одну з: {supported}."
        return (
            f"No benchmark stored for '{metric_name}'. "
            f"Try one of: {supported}."
        )

    if lang == "uk":
        return (
            f"Бенчмарк: {key.upper()}\n"
            f"- Що вимірює: {data['description']}\n"
            f"- Добре / ціль: {data['good']}\n"
            f"- Типовий діапазон: {data['typical']}\n"
            f"- На що звернути увагу: {data['watchout']}\n"
            f"Примітка: діапазони — орієнтовні емпіричні правила SaaS, а не аудійовані галузеві дані."
        )

    return (
        f"Benchmark: {key.upper()}\n"
        f"- What it measures: {data['description']}\n"
        f"- Good / target: {data['good']}\n"
        f"- Typical range: {data['typical']}\n"
        f"- Watch out: {data['watchout']}\n"
        f"Note: ranges are illustrative SaaS rules of thumb, not audited industry data."
    )


@tool
def get_live_metric(metric_name: str, lang: str = "en") -> str:
    """Return the company's CURRENT/actual value for a metric, computed from
    live data (not a definition or benchmark). Use this whenever the user asks
    about "our", "current", "actual", "right now", "наш", "поточний", "зараз" —
    i.e. real numbers, not general SaaS knowledge.

    Args:
        metric_name: one of mrr, arr, arpu, active_customers,
            mom_mrr_growth_pct, logo_churn_rate_pct.
        lang: "en" or "uk".
    """
    # Imported lazily to avoid a hard dependency for callers that never use this tool.
    from metrics.snapshot_service import read_snapshot

    snap = read_snapshot()
    if not snap:
        return (
            "Немає живого снепшоту метрик — треба запустити refresh (python -m metrics.snapshot_service)."
            if lang == "uk"
            else "No live metrics snapshot available yet — run the refresh job (python -m metrics.snapshot_service)."
        )

    key = metric_name.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"customers": "active_customers", "growth": "mom_mrr_growth_pct", "churn": "logo_churn_rate_pct"}
    key = aliases.get(key, key)

    if key not in snap or snap[key] is None:
        available = ", ".join(k for k in snap if k not in {"as_of", "generated_at"})
        if lang == "uk":
            return f"Метрика '{metric_name}' недоступна в живих даних. Доступні: {available}."
        return f"Metric '{metric_name}' not available in live data. Available: {available}."

    value = snap[key]
    as_of = snap["as_of"]

    if lang == "uk":
        return f"{key} (станом на {as_of}): {value}"
    return f"{key} (as of {as_of}): {value}"


# ---------------------------------------------------------------------------
# Financial statement helpers (not LangChain tools)
# ---------------------------------------------------------------------------

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


def normalize_financial_dataframe(df: "pd.DataFrame") -> "pd.DataFrame":
    """Normalize Excel/CSV financial statements into a clean analysis-ready table."""

    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("normalize_financial_dataframe expects a pandas DataFrame")

    out = df.copy()
    out = out.dropna(axis=0, how="all").dropna(axis=1, how="all")

    if out.empty:
        return out

    scan = out.fillna("").astype(str)
    year_regex = re.compile(r"(?:19|20)\d{2}")

    def _count_years(values) -> int:
        return sum(bool(year_regex.search(str(v))) for v in values)

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
            bool(str(v).strip()) and not year_regex.search(str(v))
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

            m = year_regex.search(value)

            if m:
                year = m.group()

                if year in seen_years:
                    seen_years[year] += 1
                    year = f"{year}_{seen_years[year]}"
                else:
                    seen_years[year] = 0

                new_columns.append(year)

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

        if year_regex.fullmatch(label):
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


def _extract_year_number(name: object) -> Optional[int]:
    match = re.search(r"(?:19|20)\d{2}", str(name))
    return int(match.group()) if match else None


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
    raw, err = _load_csv(file_path)
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

def _infer_financial_statement_args(file_path: str, question: str) -> dict:
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
            
            # Clean trailing year/fluff from the total part
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
    # Step A: Priority matching with KNOWN_ITEMS
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
        # Step B: Fallback string cleaning (fluff removal)
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

    Prefer this over get_csv_agent / csv_row_sum for financial-statement questions
    about a specific line item, period values, year comparisons, YoY growth, or
    checking whether a total equals the sum of its components.

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
            # Relative tolerance for floating/rounding differences in exports.
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
