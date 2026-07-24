# MRR — Щомісячний повторюваний дохід (Monthly Recurring Revenue)

## Визначення

Monthly Recurring Revenue (MRR) — це прогнозований дохід, який передплатний бізнес очікує отримувати щомісяця від активних підписок. MRR приводить усі повторювані платежі до щомісячного еквіваленту і є ключовою метрикою "здоров'я" виручки для SaaS та інших передплатних моделей.

## Формула

```
MRR = Σ (щомісячна плата за кожну активну підписку)
```

Для нещомісячних тарифів:

```
MRR з річного плану = Річна вартість контракту / 12
MRR з квартального плану = Квартальна плата / 3
```

Основні компоненти:

```
New MRR       = MRR від нових клієнтів за період
Expansion MRR = MRR від апгрейдів, додаткових опцій чи місць
Contraction MRR = MRR, втрачений через даунгрейди
Churned MRR   = MRR, втрачений через скасування
Net New MRR   = New MRR + Expansion MRR − Contraction MRR − Churned MRR
```

Міст (bridge) кінцевого MRR:

```
Ending MRR = Beginning MRR + New MRR + Expansion MRR − Contraction MRR − Churned MRR
```

## Бізнес-інтерпретація

- **Сигнал зростання:** зростання MRR означає розширення повторюваної бази; падіння — сигнал відтоку чи скорочення.
- **Передбачуваність:** що більша частка виручки в MRR, то легше прогнозувати грошовий потік порівняно з разовими продажами.
- **Зв'язок з юніт-економікою:** порівнюй MRR з CAC, LTV і churn, щоб оцінити ефективність зростання.
- **Сегментація:** розбивай MRR за планом, когортою, регіоном чи каналом, щоб знайти джерела зростання або ризику.
- **Перевірка якості:** Net New MRR і утримання наявного MRR важливіші за зростання, яке тримається лише на агресивних знижках.

## Типові помилки

1. Включення разових платежів (сетап, послуги, обладнання) у MRR.
2. Врахування повного річного інвойсу як MRR замість поділу на 12.
3. Змішування визнаної виручки (GAAP) з контрактним/booked MRR без позначення різниці.
4. Ігнорування апгрейдів/даунгрейдів чи пропорцій у середині періоду під час побудови MRR bridge.
5. Врахування призупинених чи прострочених підписок як повністю активного MRR без чіткої політики.
6. Подвійний підрахунок місць чи додаткових опцій, які вже входять до базової підписки.
7. Звітування лише про Gross New MRR без урахування churn/contraction.

## Поради для співбесіди

- Чітко визнач MRR перед формулами — інтерв'юери часто перевіряють саме точність визначення.
- Завжди розрізняй **New / Expansion / Contraction / Churned / Net New MRR**.
- Згадай, як річні та багаторічні угоди конвертуються в MRR (поділ на 12 / 36 тощо).
- Пов'яжи MRR з **ARR** (`ARR = MRR × 12`) та з churn (`Churned MRR / Beginning MRR`).
- Будь готовий пояснити граничні випадки: тріали, freemium, знижки, повернення коштів, мультипродуктові акаунти.
- Покажи, що вмієш побудувати **MRR bridge** від початкового до кінцевого MRR за місяць.

## Приклад SQL

```sql
-- Щомісячний зріз MRR по клієнтах (усі плани приведені до місячного еквіваленту)
WITH subscriptions_normalized AS (
    SELECT
        s.customer_id,
        s.subscription_id,
        s.plan_name,
        s.status,
        s.start_date,
        s.end_date,
        CASE s.billing_interval
            WHEN 'month' THEN s.amount
            WHEN 'quarter' THEN s.amount / 3.0
            WHEN 'year' THEN s.amount / 12.0
            ELSE NULL
        END AS mrr_amount
    FROM subscriptions s
    WHERE s.status = 'active'
)
SELECT
    DATE_TRUNC('month', CURRENT_DATE) AS mrr_month,
    customer_id,
    SUM(mrr_amount) AS customer_mrr
FROM subscriptions_normalized
GROUP BY 1, 2
ORDER BY customer_mrr DESC;
```

Ескіз MRR bridge:

```sql
-- Ілюстративно: порівняння початкового та кінцевого активного MRR за місяць
SELECT
    SUM(CASE WHEN event_type = 'new' THEN mrr_delta ELSE 0 END) AS new_mrr,
    SUM(CASE WHEN event_type = 'expansion' THEN mrr_delta ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN event_type = 'contraction' THEN mrr_delta ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN event_type = 'churn' THEN mrr_delta ELSE 0 END) AS churned_mrr
FROM mrr_events
WHERE event_month = DATE '2026-06-01';
```

## Джерела

- Огляди SaaS-метрик (фреймворки MRR / ARR / churn, якими користуються оператори та інвестори)
- Внутрішня політика визнання виручки vs booked MRR (специфічна для компанії)
- Документація білінгових систем (Stripe, Chargebee, Recurly тощо) щодо пропорцій і статусів
