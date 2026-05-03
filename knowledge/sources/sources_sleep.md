# Sources — Sleep & Circadian

## Best for
Проблемы со сном, режим, оптимизация восстановления, HRV/RHR интерпретация через призму сна.

**Tier 2:** Matthew Walker (Why We Sleep, научные работы по сну)
**Tier 3:** Huberman (протоколы, циркадный ритм, свет)

При конфликте → Walker / Tier 1 guidelines первичны.

---

## Protocols we use IN THIS Health OS

**directives.yaml:**
- `sleep.target_hours_min: 7` — минимум 7 ч avg; <7h → Sleep debt flag
- `sleep.caffeine_cutoff_hours: 10` — кофеин не позже (время сна − 10ч)
- `sleep.bedtime_variance_max_min: 30` — регулярность ±30 мин важнее длины

**strategy.md:**
- Расписание тренировок не конфликтует со сном: силовые Mon/Wed/Fri утром или после работы
- Если сон <6ч → тренировку отменить, перейти на прогулку (правило системы #1)

**Recovery Gate:**
- sleep_avg ≥7h → вклад в GREEN
- sleep_avg 6.0–6.99h → YELLOW (−30% объёма силовых, нет интервалов)
- sleep_avg <6h → RED (только техника/ходьба, maintenance питание)
- Sleep debt flag (avg <7h ИЛИ ≥2 ночей <6h) → питание: maintenance, без дефицита

**Environment:**
- `environment.morning_light` до 10:00 → якорит циркадный ритм → улучшает sleep onset
- `environment.daylight_minutes` < 30 → дополнительный стресс на ритм → кофеин строже на 1ч

---

## Metrics to track
- `sleep.avg_sleep_hours` (week_*.yaml) — ключевой для Recovery Gate
- `sleep.avg_bedtime` + `bedtime_variance_min` — регулярность
- `cardiovascular.avg_hrv_ms` + `avg_resting_hr` — прокси качества сна
- `environment.morning_light_days` (0–7) — из daily logs

---

## Common misreads / what to ignore
- "Спать меньше, но качественнее" — не работает системно, HRV не обманешь
- Мелатонин как замена режима — только как инструмент при смене часового пояса
- "Алкоголь помогает уснуть" — REM подавляется, HRV падает

---

## Evidence notes
- Walker: хроническое <7h → ↑ApoB риск, ↓иммунитет, ↑кортизол → проверять через HRV/RHR еженедельно
- Huberman: утренний свет 10–30 мин — Tier 3 протокол, но механизм (SCN/меланопсин) Tier 1 подтверждён
- Если HRV стабильно низкий при нормальном сне → искать другой стрессор (питание, нагрузка, CRP)
- Приоритет анализов: CRP (уже есть 5.1 — elevated) влияет на качество сна; снижение CRP = цель
