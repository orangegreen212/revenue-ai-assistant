---
title: SQL-запити для аналітики утримання
category: SQL
metric: null
difficulty: Intermediate
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - churn
  - nrr
  - grr
  - retention-queries
---

# Визначення

Цей документ збирає стандартні SQL-патерни для розрахунку logo churn, revenue churn та когортних NRR/GRR з місячних зрізів MRR.

# Чому це важливо

Метрики утримання легко тонко зіпсувати в SQL — особливо різницю між використанням кількості клієнтів на початок чи на кінець періоду як знаменника, і коректне виключення нових клієнтів з NRR/GRR.

# Формула

Припущена схема:

```
mrr_snapshots(customer_id, snapshot_date, mrr, status)
```

# Приклад

**Logo churn і revenue churn за один місяць:**

```sql
WITH start_customers AS (
    SELECT customer_id, mrr AS start_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-06-01'
      AND status = 'active'
),
churned AS (
    SELECT s.customer_id, s.start_mrr
    FROM start_customers s
    LEFT JOIN mrr_snapshots e
      ON s.customer_id = e.customer_id
     AND e.snapshot_date = DATE '2026-07-01'
    WHERE e.customer_id IS NULL OR e.mrr = 0
)
SELECT
    (SELECT COUNT(*) FROM churned) * 1.0
        / NULLIF((SELECT COUNT(*) FROM start_customers), 0) AS logo_churn_rate,
    (SELECT SUM(start_mrr) FROM churned) * 1.0
        / NULLIF((SELECT SUM(start_mrr) FROM start_customers), 0) AS revenue_churn_rate;
```

**Когортний NRR за один період:**

```sql
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-07-01'
    GROUP BY customer_id
)
SELECT
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) AS nrr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
-- Примітка: нові клієнти, залучені після початкового зрізу, коректно
-- виключені тут, бо запит проходить лише по початковій когорті.
```

**Когортний GRR (expansion виключений, обмежений 100%):**

```sql
WITH beginning AS (
    SELECT customer_id, SUM(mrr) AS begin_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
    GROUP BY customer_id
),
ending AS (
    SELECT customer_id, SUM(mrr) AS end_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-07-01'
    GROUP BY customer_id
)
SELECT
    SUM(LEAST(COALESCE(e.end_mrr, 0), b.begin_mrr)) / NULLIF(SUM(b.begin_mrr), 0) AS grr
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
```

# Типові помилки

- Використання списку клієнтів з кінцевого зрізу як бази для churn замість початкового — це занижує churn.
- Забути `LEAST(...)` у запиті GRR, через що expansion "просочується" й піднімає GRR понад 100%.
- Включення клієнтів, які приєднались **після** початкового зрізу, у когортний запит NRR/GRR — `beginning` CTE має бути єдиним джерелом списку клієнтів для join.

# Пов'язані метрики

- **Churn Rate, NRR, GRR** — метрики, які ці запити рахують напряму.
- **Cohort Analysis** — методологія, яку ці запити реалізують у SQL.

# Джерела

- Синтезовані стандартні SQL-патерни, поширені в документації SaaS-аналітики (синтезовано, не цитується дослівно).

*Примітка: це ілюстративні шаблони; продакшн-схеми та граничні випадки (зміни тарифу посеред періоду, пропорції) потребуватимуть адаптації.*
