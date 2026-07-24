# NRR — Чисте утримання виручки (Net Revenue Retention)

## Визначення

Net Revenue Retention (NRR), також відомий як Net Dollar Retention (NDR), вимірює, як змінюється повторювана виручка від наявної когорти клієнтів з часом після expansion, contraction і churn. Відповідає на питання: скільки з ARR/MRR, що ми мали від клієнтів на початку періоду, у нас залишилося від тих самих клієнтів наприкінці — включно з апгрейдами й даунгрейдами?

## Формула

```
NRR = (Beginning ARR + Expansion − Contraction − Churn) / Beginning ARR
```

Часто у відсотках:

```
NRR % = NRR × 100
```

Еквівалентна когортна форма:

```
NRR = Кінцевий ARR початкової когорти / Початковий ARR початкової когорти
```

Примітка: нові клієнти, залучені протягом періоду, виключаються з NRR; вони належать до New ARR / метрик зростання логотипів.

## Бізнес-інтерпретація

NRR — один з найсильніших сигналів product-market fit і здоров'я розширення акаунтів. NRR понад 100% означає, що expansion від наявних клієнтів більш ніж компенсує churn і даунгрейди — база зростає навіть без нових логотипів. Найкращі B2B SaaS компанії часто цілять NRR 110–130%+. NRR нижче 100% означає, що наявна база скорочується, і зростання повністю залежить від нових залучень. Сегментуй NRR за планом, розміром компанії та когортою, щоб знайти, де концентрується expansion чи churn.

## Типові помилки

- Включення нових клієнтів, залучених у періоді, до когорти NRR.
- Використання термінів визнання виручки замість підписного ARR/MRR для когорти.
- Ігнорування contraction (даунгрейдів) і врахування лише повного churn.
- Порівняння NRR між компаніями без узгодження вікон (місячне vs trailing-twelve-month).
- Святкування високого NRR при серйозному logo churn (кілька великих expansion маскують багато втрачених акаунтів).

## Поради для співбесіди

**Q:** Що означає NRR > 100%, і чим це відрізняється від GRR?

**A:** NRR > 100% означає, що виручка від expansion у початковій когорті перевищує втрати від churn і contraction, тож утримана виручка зростає. GRR (Gross Revenue Retention) виключає expansion і обмежений 100% — він вимірює лише те, скільки з початкової виручки залишилося до апгрейдів. Використовуй GRR для якості утримання, а NRR — для чистого зростання від наявної бази.

## Приклад SQL

```sql
-- Спрощений місячний NRR для когорти клієнтів, активних на початок місяця
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
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) AS nrr,
    SUM(COALESCE(e.end_mrr, 0)) / NULLIF(SUM(b.begin_mrr), 0) * 100 AS nrr_pct
FROM beginning b
LEFT JOIN ending e ON b.customer_id = e.customer_id;
```

## Джерела

- Документація Stripe Billing
- Посібник Paddle SaaS Metrics
