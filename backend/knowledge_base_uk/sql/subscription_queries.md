---
title: SQL-запити для аналітики підписок
category: SQL
metric: null
difficulty: Beginner
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - subscriptions
  - arpu
  - cac
  - subscription-queries
---

# Визначення

Цей документ збирає SQL-патерни для аналізу на рівні підписок: ARPU за тарифом, кількість активних підписок і blended CAC.

# Чому це важливо

Це найчастіше використовувані запити для рішень щодо ціноутворення, аналізу міксу тарифів та огляду ефективності залучення — вони перетворюють сирі дані про підписки й витрати в метрики на клієнта/тариф, які реально переглядає керівництво.

# Формула

Припущена схема (додатково до `subscriptions`):

```
customers(customer_id, first_paid_date)
sales_marketing_costs(spend_date, amount)
```

# Приклад

**ARPU за тарифом:**

```sql
SELECT
    plan_name,
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year'    THEN amount / 12.0
            ELSE NULL
        END
    ) / NULLIF(COUNT(DISTINCT customer_id), 0) AS arpu
FROM subscriptions
WHERE status = 'active'
GROUP BY plan_name
ORDER BY arpu DESC;
```

**Кількість активних підписок за тарифом:**

```sql
SELECT
    plan_name,
    COUNT(*) AS active_subscriptions
FROM subscriptions
WHERE status = 'active'
GROUP BY plan_name
ORDER BY active_subscriptions DESC;
```

**Blended CAC за місяцем:**

```sql
WITH new_customers AS (
    SELECT
        DATE_TRUNC('month', first_paid_date) AS cohort_month,
        COUNT(DISTINCT customer_id) AS new_customer_count
    FROM customers
    WHERE first_paid_date IS NOT NULL
    GROUP BY 1
),
sm_spend AS (
    SELECT
        DATE_TRUNC('month', spend_date) AS spend_month,
        SUM(amount) AS sm_cost
    FROM sales_marketing_costs
    GROUP BY 1
)
SELECT
    n.cohort_month,
    s.sm_cost,
    n.new_customer_count,
    s.sm_cost / NULLIF(n.new_customer_count, 0) AS cac
FROM new_customers n
JOIN sm_spend s ON n.cohort_month = s.spend_month
ORDER BY n.cohort_month;
```

# Типові помилки

- Розрахунок ARPU через `COUNT(*)` замість `COUNT(DISTINCT customer_id)`, що завищує кількість клієнтів з кількома активними підписками.
- Приєднання кількості нових клієнтів до витрат за календарним місяцем без урахування лагу між витратами й конверсією — точніша модель відносить витрати до когорти, на яку вони реально вплинули.
- Змішування платного й органічного залучення в "blended CAC", коли насправді потрібен CAC на рівні каналу.

# Пов'язані метрики

- **ARPU, CAC** — метрики, які ці запити рахують напряму.
- **Customer Segmentation** — розбивка за тарифом — базова форма сегментації.

# Джерела

- Синтезовані стандартні SQL-патерни, поширені в документації SaaS-аналітики (синтезовано, не цитується дослівно).

*Примітка: ілюстративні шаблони; адаптуй назви таблиць/колонок і логіку атрибуції під свою реальну схему білінгу й маркетингових витрат.*
