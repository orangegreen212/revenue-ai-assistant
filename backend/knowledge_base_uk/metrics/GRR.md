# GRR — Валове утримання виручки (Gross Revenue Retention)

## Визначення

Gross Revenue Retention (GRR), також відоме як Gross Dollar Retention, вимірює, скільки повторюваної виручки від наявної когорти клієнтів утримано після churn і contraction — **виключаючи** expansion. Ізолює якість утримання початкової бази виручки без "заліку" за апсели.

## Формула

```
GRR = (Beginning ARR − Contraction − Churn) / Beginning ARR
```

У відсотках:

```
GRR % = GRR × 100
```

Зв'язок з NRR:

```
NRR = GRR + (Expansion / Beginning ARR)
```

GRR обмежений 100%, бо expansion виключений.

## Бізнес-інтерпретація

GRR відповідає на питання, чи утримуєш ти виручку, яку вже мав. Високий GRR (часто 85–95%+ на рік для здорового B2B SaaS) означає низький churn і обмежені даунгрейди. Слабкий GRR при сильному NRR може означати, що кілька великих expansion маскують широкі проблеми утримання. Продуктові, CS та фінансові команди використовують GRR для моніторингу здоров'я акаунтів незалежно від апсел-активностей. Відстежуй GRR за сегментом (SMB vs mid-market vs enterprise), бо динаміка churn сильно відрізняється залежно від розміру клієнта.

## Типові помилки

- Включення потенціалу expansion у GRR (це належить лише до NRR).
- Звітування про GRR понад 100% — за визначенням він не може перевищувати 100%.
- Змішування утримання логотипів з утриманням виручки без уточнення метрики.
- Використання різних когортних вікон (місячне vs TTM) при бенчмаркінгу проти конкурентів.
- Ігнорування contraction від скорочення місць і даунгрейдів планів.

## Поради для співбесіди

**Q:** Чому GRR ніколи не може перевищувати 100%, а NRR може?

**A:** GRR лише віднімає churn і contraction від початкової виручки; він не дає "заліку" за апгрейди чи додаткові опції, тож найкращий сценарій — утримати 100% початкової бази. NRR додає expansion, тож утримана виручка може зростати понад початкову базу і перевищувати 100%.

## Приклад SQL

```sql
-- Місячний GRR: утриманий MRR з початкової когорти, без урахування expansion
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
        / NULLIF(SUM(b.begin_mrr), 0) AS grr,
    SUM(LEAST(COALESCE(e.end_mrr, 0), b.begin_mrr))
        / NULLIF(SUM(b.begin_mrr), 0) * 100 AS grr_pct
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
```

## Джерела

- Документація Stripe Billing
- Посібник Paddle SaaS Metrics
