"""KPI calculation, benchmark reference data, and live-metric lookup tools."""

from typing import Optional

from langchain_core.tools import tool

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
    except Exception as exc:  # noqa: BLE001
        if uk:
            return f"Помилка розрахунку KPI '{kpi_name}': {exc}"
        return f"Error calculating KPI '{kpi_name}': {exc}"

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
