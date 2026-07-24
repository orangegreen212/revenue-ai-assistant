# Churn — Відтік клієнтів та виручки

## Визначення

Churn вимірює темп, з яким клієнти або повторювана виручка "йдуть" за період. **Logo (клієнтський) churn** рахує втрачені акаунти; **revenue churn** вимірює втрачений MRR/ARR через скасування (а іноді й даунгрейди, залежно від визначення). Churn — центральна метрика ризику утримання для передплатних бізнесів.

## Формула

Клієнтський (logo) churn:

```
Logo Churn Rate = Клієнти, втрачені за період / Клієнти на початок періоду
```

Revenue churn:

```
Revenue Churn Rate = Втрачений MRR за період / MRR на початок періоду
```

Gross vs net revenue churn:

```
Gross Revenue Churn = (Churned MRR + Contraction MRR) / Beginning MRR
Net Revenue Churn   = (Churned MRR + Contraction MRR − Expansion MRR) / Beginning MRR
```

Приблизна тривалість життя клієнта:

```
Середня тривалість (місяців) ≈ 1 / Місячний logo churn rate
```

## Бізнес-інтерпретація

Низький churn підсилює зростання: кожен пункт зниження churn покращує LTV, NRR і надійність прогнозу. SMB-продукти часто мають вищий місячний logo churn; enterprise зазвичай має нижчий logo churn, але великий вплив на виручку від втрати одного акаунта. Завжди розділяй добровільний churn (скасування) та вимушений (невдалі платежі) — виправлення різні (продукт/CS vs dunning). Звітуй churn за когортою, планом і терміном перебування; ранній churn часто домінує.

## Типові помилки

- Змішування logo churn і revenue churn в одній наративі без позначень.
- Використання кількості клієнтів на кінець періоду як знаменника замість початкової кількості.
- Неправильна анаулізація місячного churn (`12 × місячний` завищує; краще `1 − (1 − m)^12`).
- Врахування даунгрейдів як повного churn (або повне ігнорування їх).
- Приховування вимушеного churn всередині "загального churn" без окремого погляду на відновлення платежів.

## Поради для співбесіди

**Q:** У чому різниця між logo churn і revenue churn? Що важливіше?

**A:** Logo churn — це % втрачених клієнтів; revenue churn — % втраченого MRR/ARR. Revenue churn зазвичай важливіший для фінансового планування, бо втрата одного enterprise-акаунта може переважити багато SMB-логотипів. Проте варто відстежувати обидва: високий logo churn при низькому revenue churn може означати нестабільність SMB, тоді як база виручки виглядає нормально. Пов'яжи відповідь з NRR/GRR, коли говориш про утримання виручки.

## Приклад SQL

```sql
-- Місячний logo churn та revenue churn
WITH start_customers AS (
    SELECT customer_id, mrr AS start_mrr
    FROM mrr_snapshots
    WHERE snapshot_date = DATE '2026-01-01'
),
churned AS (
    SELECT c.customer_id, c.start_mrr
    FROM start_customers c
    LEFT JOIN mrr_snapshots e
      ON c.customer_id = e.customer_id
     AND e.snapshot_date = DATE '2026-02-01'
    WHERE e.customer_id IS NULL OR e.mrr = 0
)
SELECT
    (SELECT COUNT(*) FROM churned) * 1.0
        / NULLIF((SELECT COUNT(*) FROM start_customers), 0) AS logo_churn_rate,
    (SELECT SUM(start_mrr) FROM churned) * 1.0
        / NULLIF((SELECT SUM(start_mrr) FROM start_customers), 0) AS revenue_churn_rate;
```

## Джерела

- Документація Stripe Billing
- Посібник Paddle SaaS Metrics
