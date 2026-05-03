# Sources — Strength & Hypertrophy

## Best for
Объём тренировок, прогрессия, замена упражнений, минимумы для сохранения мышц на дефиците.

**Tier 2:** Brad Schoenfeld (volume/intensity research), Eric Helms / 3DMJ (evidence-based natural lifting)
**Tier 3:** Mike Israetel (volume landmarks), Jeff Nippard (практические видео)

При конфликте → Schoenfeld / Helms / Tier 1 мета-анализы первичны.

---

## Protocols we use IN THIS Health OS

**directives.yaml:**
- `training.min_strength_sessions_week: 3` — минимум для сохранения мышц на дефиците
- `training.banned_exercises: []` — заполнять при травмах
- Замена упражнения: ТОЛЬКО внутри паттерна (Squat↔Squat, Hinge↔Hinge, Push↔Push, Pull↔Pull)

**strategy.md / program.yaml:**
- Full Body 3x/нед: A (Leg Press, RDL, Bench, Cable Row) / B (Goblet, Deadlift, OHP, Lat PD) / C (Bulgarian, Hip Thrust, Incline DB, Barbell Row)
- Двойная прогрессия: 8→12 rep, затем +2.5 кг и снова с 8
- На дефиците: объём MV–MEV (поддерживать, не растить)

**Recovery Gate:**
- 🟢 GREEN → полный план (3 сета каждого упражнения)
- 🟡 YELLOW → −30% объёма: 2 сета вместо 3, RPE −1
- 🔴 RED → только техника: 1 лёгкий сет, акцент на паттерне, без нагрузки

**supplements (через directives/strategy):**
- Омега-3 ≥2г/день — поддержка mTOR + анти-воспаление (CRP 5.1 elevated)
- Адекватный белок: 160г/день (2.03 г/кг) — из strategy.md

---

## Metrics to track
- `training.strength_sessions_count` (week_*.yaml) — цель: 3/нед
- Прогрессия в program.yaml: веса и повторения по упражнениям
- `body.weight_trend_7d` — при дефиците −0.3..−0.5 кг/нед целевой диапазон
- ALMI (InBody) — следующий тест: ⚠️ данных нет

---

## Common misreads / what to ignore
- "На дефиците нельзя прогрессировать" — нельзя растить, но прогрессия навыка и лёгкий прирост у начинающих возможен
- "Больше объёма = лучше" — на дефиците и при YELLOW/RED → нет; MRV важен
- Israetel (Tier 3): volume landmarks полезны как ориентир, не как жёсткий закон

---

## Evidence notes
- Schoenfeld мета-анализ: ≥10 сетов/мышцу/нед для гипертрофии; на дефиците ориентир MV ~5–8 сетов
- Helms: белок 2.2–3.1 г/кг при дефиците — мы на 2.03, в пределах нормы
- Grip strength — longevity маркер: ⚠️ данных нет → динамометр при следующем визите
- При RED Recovery Gate силовая тренировка "в полную" → риск перегруза выше пользы; Tier 1 данные поддерживают снижение объёма при стрессе
