# Payback Period — Термін окупності CAC

## Визначення

CAC Payback Period — кількість місяців, необхідна валовому прибутку від нового клієнта (чи когорти), щоб окупити вартість його залучення. Пов'язує CAC, ARPU та валову маржу в часову шкалу грошової ефективності зростання.

## Формула

```
CAC Payback (місяців) = CAC / (ARPU × Валова маржа %)
```

Через MRR на клієнта:

```
Payback = CAC / (Середній MRR на нового клієнта × Валова маржа %)
```

Когортна форма:

```
Payback = місяці до моменту, коли накопичений валовий прибуток когорти ≥ CAC, витрачений на її залучення
```

## Бізнес-інтерпретація

Коротший payback означає швидше повернення витрачених на залучення коштів і більше можливостей реінвестувати у зростання. Багато SaaS-команд цілять payback менше ~12 місяців (іноді жорсткіше для SMB/PLG, довше прийнятно для enterprise з високим LTV). Довгий payback усе ще може працювати, якщо LTV високий і є доступний капітал — але це підвищує фінансовий ризик. Відстежуй payback за каналом і сегментом: платна реклама в соцмережах може окупатися за 4 місяці, а outbound-продажі enterprise — за 18.

## Типові помилки

- Використання виручки замість валового прибутку в знаменнику (занижує payback).
- Змішування річного CAC з місячним ARPU без конвертації одиниць.
- Ігнорування того, що перші місяці можуть включати знижки, безкоштовні місяці чи онбординг-кредити.
- Використання blended CAC/ARPU, коли payback сильно різниться між каналами.
- Забуття про лаг циклу продажів: CAC витрачається до того, як клієнт стає платним.

## Поради для співбесіди

**Q:** Як порахувати CAC payback, і чому це цікавить інвесторів?

**A:** `Payback = CAC / (ARPU × Валова маржа %)`. Інвестори звертають на це увагу, бо це показує, як довго зростання "з'їдає" готівку, перш ніж клієнти самі почнуть фінансувати своє залучення. Швидкий payback підтримує ефективне масштабування; довгий payback потребує сильнішого обґрунтування через LTV та більше капіталу. Завжди вказуй припущення щодо маржі та чи CAC є повністю навантаженим.

## Приклад SQL

```sql
-- Приблизний payback за когортою місяця залучення
WITH cohort AS (
    SELECT
        DATE_TRUNC('month', first_paid_date) AS cohort_month,
        COUNT(DISTINCT customer_id) AS new_customers,
        AVG(starting_mrr) AS avg_starting_mrr
    FROM customers
    WHERE first_paid_date IS NOT NULL
    GROUP BY 1
),
cac AS (
    SELECT
        DATE_TRUNC('month', spend_date) AS spend_month,
        SUM(amount) AS sm_cost
    FROM sales_marketing_costs
    GROUP BY 1
)
SELECT
    c.cohort_month,
    cac.sm_cost / NULLIF(c.new_customers, 0) AS cac,
    c.avg_starting_mrr,
    (cac.sm_cost / NULLIF(c.new_customers, 0))
        / NULLIF(c.avg_starting_mrr * 0.80, 0) AS payback_months_80pct_margin
FROM cohort c
JOIN cac ON c.cohort_month = cac.spend_month
ORDER BY c.cohort_month;
```

## Джерела

- Документація Stripe Billing
- Посібник Paddle SaaS Metrics
