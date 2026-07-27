---
title: SQL-запити для аналітики виручки
category: SQL
metric: null
difficulty: Intermediate
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - mrr
  - arr
  - revenue-queries
---

# Визначення

Цей документ збирає стандартні патерни SQL-запитів для розрахунку MRR, ARR і руху виручки (MRR bridge) з типової таблиці підписок. Назви таблиць і колонок ілюстративні — адаптуй їх під свою реальну схему.

# Чому це важливо

MRR і ARR — найчастіше перераховувані числа в стеку SaaS-аналітики, і помилка в логіці нормалізації інтервалів (наприклад, неконвертування річного білінгу в місячний еквівалент) — одне з найпоширеніших джерел некоректних дашбордів.

# Формула

Припущена схема:

```
subscriptions(
  customer_id, subscription_id, plan_name,
  status, billing_interval, amount,
  start_date, end_date
)
```

# Приклад

**Поточний MRR, нормалізований за інтервалами білінгу:**

```sql
SELECT
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year'    THEN amount / 12.0
            ELSE NULL
        END
    ) AS total_mrr
FROM subscriptions
WHERE status = 'active';
```

**Поточний ARR (анаулізований):**

```sql
SELECT
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount * 12
            WHEN 'quarter' THEN amount * 4
            WHEN 'year'    THEN amount
            ELSE NULL
        END
    ) AS total_arr
FROM subscriptions
WHERE status = 'active';
```

**MRR за клієнтом:**

```sql
SELECT
    customer_id,
    SUM(
        CASE billing_interval
            WHEN 'month'   THEN amount
            WHEN 'quarter' THEN amount / 3.0
            WHEN 'year'    THEN amount / 12.0
            ELSE NULL
        END
    ) AS customer_mrr
FROM subscriptions
WHERE status = 'active'
GROUP BY customer_id
ORDER BY customer_mrr DESC;
```

**Bridge руху MRR між двома датами зрізу** (припускає таблицю `mrr_snapshots(customer_id, snapshot_date, mrr)`):

```sql
WITH beginning AS (
    SELECT customer_id, mrr AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-06-01'
),
ending AS (
    SELECT customer_id, mrr AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-07-01'
)
SELECT
    SUM(CASE WHEN b.customer_id IS NULL THEN e.end_mrr ELSE 0 END) AS new_mrr,
    SUM(CASE WHEN e.end_mrr > b.begin_mrr THEN e.end_mrr - b.begin_mrr ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN e.end_mrr < b.begin_mrr AND e.end_mrr > 0 THEN b.begin_mrr - e.end_mrr ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN e.customer_id IS NULL OR e.end_mrr = 0 THEN b.begin_mrr ELSE 0 END) AS churned_mrr
FROM beginning b
FULL OUTER JOIN ending e ON b.customer_id = e.customer_id;
```

# Типові помилки

- Забути нормалізувати `billing_interval` перед сумуванням — пряме додавання місячних і річних сум завищує MRR.
- Фільтрація лише за `status = 'active'` без перевірки `end_date`, що може подвійно врахувати підписки, скасовані, але ще не позначені неактивними.
- Використання `INNER JOIN` замість `FULL OUTER JOIN` у bridge-запиті, що тихо викидає нових чи повністю churned клієнтів з результату.

# Пов'язані метрики

- **MRR / ARR** — метрики, які ці запити рахують напряму.
- **Churn Rate** — див. `retention_queries.md` для SQL-патернів саме про churn.

# Джерела

- Синтезовані стандартні SQL-патерни, поширені в документації SaaS-аналітики та посібниках білінгових платформ (Stripe, Chargebee, Recurly — синтезовано, не цитується дослівно).

*Примітка: точні назви таблиць і колонок відрізнятимуться залежно від схеми; ці запити — ілюстративні шаблони, не прив'язані до конкретної продакшн-бази.*
