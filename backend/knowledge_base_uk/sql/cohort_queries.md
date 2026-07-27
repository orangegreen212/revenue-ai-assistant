---
title: SQL-запити для когортного аналізу
category: SQL
metric: null
difficulty: Advanced
source:
  - Synthesized standard patterns for SaaS revenue analytics
tags:
  - sql
  - cohort-analysis
  - retention
  - cohort-queries
---

# Визначення

Цей документ збирає SQL-патерни для побудови таблиць когортного утримання — групування клієнтів за місяцем реєстрації й відстеження їхнього утримання в наступні місяці — SQL-реалізацію фреймворку когортного аналізу.

# Чому це важливо

Когортні таблиці — один зі складніших стандартних запитів у SaaS-аналітиці, бо вони вимагають генерації повної сітки комбінацій (місяць когорти × місяць спостереження), а не просто однієї агрегації — наївний `GROUP BY` сам по собі не може дати таку форму.

# Формула

Припущена схема:

```
customers(customer_id, signup_date)
mrr_snapshots(customer_id, snapshot_date, mrr, status)
```

# Приклад

**Таблиця logo-утримання когорт (% кожної когорти, що все ще активна через N місяців після реєстрації):**

```sql
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT
        m.customer_id,
        c.cohort_month,
        DATE_TRUNC('month', m.snapshot_date) AS activity_month,
        (DATE_PART('year', m.snapshot_date) - DATE_PART('year', c.cohort_month)) * 12
            + (DATE_PART('month', m.snapshot_date) - DATE_PART('month', c.cohort_month)) AS months_since_signup
    FROM mrr_snapshots m
    JOIN cohorts c ON m.customer_id = c.customer_id
    WHERE m.status = 'active'
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.months_since_signup,
    COUNT(DISTINCT a.customer_id) AS active_customers,
    cs.cohort_size,
    COUNT(DISTINCT a.customer_id) * 1.0 / NULLIF(cs.cohort_size, 0) AS retention_rate
FROM activity a
JOIN cohort_sizes cs ON a.cohort_month = cs.cohort_month
GROUP BY a.cohort_month, a.months_since_signup, cs.cohort_size
ORDER BY a.cohort_month, a.months_since_signup;
```

**Утримання виручки когорти (у стилі NRR, за когортою й місяцем від реєстрації):**

```sql
WITH cohorts AS (
    SELECT customer_id, DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
cohort_start_mrr AS (
    SELECT c.cohort_month, SUM(m.mrr) AS starting_mrr
    FROM mrr_snapshots m
    JOIN cohorts c ON m.customer_id = c.customer_id
    WHERE DATE_TRUNC('month', m.snapshot_date) = c.cohort_month
    GROUP BY c.cohort_month
),
cohort_mrr_by_month AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC('month', m.snapshot_date) AS activity_month,
        SUM(m.mrr) AS mrr_that_month
    FROM mrr_snapshots m
    JOIN cohorts c ON m.customer_id = c.customer_id
    GROUP BY c.cohort_month, DATE_TRUNC('month', m.snapshot_date)
)
SELECT
    cb.cohort_month,
    cb.activity_month,
    cb.mrr_that_month,
    cs.starting_mrr,
    cb.mrr_that_month / NULLIF(cs.starting_mrr, 0) AS cohort_nrr
FROM cohort_mrr_by_month cb
JOIN cohort_start_mrr cs ON cb.cohort_month = cs.cohort_month
ORDER BY cb.cohort_month, cb.activity_month;
```

# Типові помилки

- Розрахунок `months_since_signup` через наївне віднімання дат замість правильної арифметики рік/місяць, що спричиняє помилки на межі років.
- Використання розміру когорти, виміряного *сьогодні*, замість розміру на момент старту когорти, що спотворює відсотки утримання для старих когорт.
- Забуття, що когортні таблиці можуть бути дуже витратними для обчислення на великих даних — попереднє агрегування в місячну таблицю зрізів (замість обчислення з сирих подій щоразу) є стандартною практикою.

# Пов'язані метрики

- **Cohort Analysis** — концептуальний фреймворк, який реалізують ці запити.
- **NRR / GRR / Churn Rate** — метрики, для візуалізації яких з часом зазвичай будуються когортні таблиці.

# Джерела

- Синтезовані стандартні SQL-патерни, поширені в документації SaaS-аналітики (синтезовано, не цитується дослівно).

*Примітка: ілюстративні шаблони на ANSI SQL date-функціях; точний синтаксис (DATE_TRUNC, DATE_PART тощо) відрізняється залежно від рушія БД (Postgres, Snowflake, BigQuery).*
