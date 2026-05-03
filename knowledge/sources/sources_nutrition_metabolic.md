# Sources — Nutrition & Metabolic Health

## Best for
Калорийный баланс, макросы, белок, энергия, когнитивная производительность через питание.

**Tier 2:** Kevin Hall (энергетический баланс, метаболическая адаптация), Spencer Nadolsky (клиническая нутрициология)
**Tier 3:** Layne Norton (практика, CICO science), Rhonda Patrick (микронутриенты, омега-3)

При конфликте → Hall / Nadolsky / Tier 1 (USDA, WHO dietary guidelines, RCT) первичны.

---

## Protocols we use IN THIS Health OS

**directives.yaml — жёсткие лимиты:**
- `nutrition.saturated_fat_limit_g: 15` — LDL-директива (CRP 5.1, LDL 3.44 elevated)
- `nutrition.omega3_minimum_g: 2` — EPA+DHA, рыба ≥2x/нед или добавка
- `nutrition.added_sugar_limit_g: 25` — когнитивный приоритет + CRP
- `sleep.caffeine_cutoff_hours: 10` — кофеин: время сна − 10ч = cutoff

**strategy.md — текущий план:**
- Калории: 2350 ккал/день (−12% от TDEE 2675)
- Белок: 160г/день (2.03 г/кг)
- Жиры: 75г/день (sat fat ≤15г)
- Углеводы: 259г/день

**Recovery Gate — корректировки:**
- 🟢 GREEN → дефицит −12% по strategy.md
- 🟡 YELLOW → maintenance или мягкий дефицит −10%
- 🔴 RED → maintenance, приоритет сон + NSDR
- Sleep debt flag → maintenance (без дефицита), calories = TDEE

**Environment-корректировка:**
- avg_daylight_minutes < 30 ИЛИ morning_light_days ≤ 2 → дефицит смягчить до −5%
  (стресс окружающей среды — не время для агрессивного дефицита)

**food_db.yaml — единственный источник КБЖУ:**
- НЕ придумывать КБЖУ вне базы → `/food-lookup` для новых продуктов
- sat fat обязателен в каждой записи

---

## Metrics to track
- `nutrition.protein_days_hit` (0–7) — цель: ≥5/7
- `nutrition.sat_fat_over_limit_days` (0–7) — цель: 0–1/7
- `nutrition.added_sugar_events` (0–7) — цель: ≤2/7
- `nutrition.avg_calories_est` — если треккаешь: сравнивать с 2350 целью
- `subjective.compliance_nutrition` (0.0–1.0) — еженедельно

---

## Common misreads / what to ignore
- "Углеводы вечером = жир" — нет, Kevin Hall: калорийный баланс определяет вес, не timing
- "Читмил разгоняет метаболизм" — краткосрочный эффект незначим; Norton: adherence важнее
- "Кето лучше для когнитивной энергии" — нет Tier 1 данных для здоровых людей при умеренном дефиците

---

## Evidence notes
- Hall (Tier 2): метаболическая адаптация реальна при агрессивном дефиците (>25%) → поэтому cap −12%
- Омега-3: EPA+DHA → снижение TG, умеренный эффект на LDL; при CRP 5.1 — anti-inflammatory приоритет
- Sat fat cap 15г: наш LDL 3.44 mmol/L (elevated по Attia) + CRP 5.1 → обоснование в directives.yaml
- Patrick: омега-3 + витамин D когнитивный эффект — Tier 3, но механизм поддержан Tier 1 данными
- Следующие анализы: HbA1c, Insulin fasting → уточнит углеводный порог
