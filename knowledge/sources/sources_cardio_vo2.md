# Sources — Cardio, Zone 2, VO2max

## Best for
Zone 2 протокол, VO2max развитие, интервальные тренировки (4×4 / 8×2), кардиориск.

**Tier 2:** Stephen Seiler (polarized training, Zone 2 / Zone 5 split, VO2max research)
**Tier 3:** Attia, Huberman, Andy Galpin (практические протоколы)

При конфликте → Seiler / Tier 1 (AHA exercise guidelines) первичны.

---

## Protocols we use IN THIS Health OS

**directives.yaml:**
- `training.min_zone2_minutes_week: 150` — жёсткий минимум; цель 150–180 мин
- Интервальная сессия: только при Recovery Gate GREEN (1 раз / 7–10 дней)

**strategy.md:**
- Zone 2: Вт/Чт/Сб, велоэрг или беговая, HR 135–150 bpm
- Прогрессия: старт 35 мин, +5 мин каждые 2 недели
- VO2max цель: ⚠️ данных нет → нужно измерить (субмаксимальный тест DDX)

**Recovery Gate:**
- 🟢 GREEN → полный Zone 2 план + 1 интервальная (4×4 или 8×2)
- 🟡 YELLOW → 90–120 мин Zone 2, ❌ интервалы отменены
- 🔴 RED → лёгкая прогулка / Zone 1, ❌ интервалы отменены
- Интервалы только на базе ≥4–6 нед регулярного Zone 2

**Environment:**
- `environment.daylight_minutes` < 30 → предпочитать outdoor Zone 2 (прогулка, велосипед)
  совмещает свет + движение — два приоритета одновременно
- Если avg_daylight_minutes < 30 → цель следующей недели +10 мин/день (через прогулку)

---

## Metrics to track
- `training.zone2_minutes_total` (week_*.yaml) — основной маркер кардиообъёма
- `training.interval_sessions_count` — максимум 1/нед при GREEN
- `cardiovascular.vo2max_estimate` — только из измерения, не оценка
- `avg_steps` — прокси общей активности

---

## Common misreads / what to ignore
- "Zone 2 — это просто медленный бег" — нет, это конкретный физиологический диапазон (fat oxidation, nasal breathing test)
- "Больше интервалов = лучше VO2max" — нет, без базы Zone 2 интервалы дают перегруз без адаптации
- Seiler: 80/20 split (80% low intensity / 20% high) — именно это мы строим

---

## Evidence notes
- Seiler (Tier 2): поляризованная модель эффективнее пирамидальной для долгосрочного VO2max
- Attia: VO2max — лучший предиктор долголетия среди измеримых маркеров (>ApoB по hazard ratio)
- VO2max ⚠️ данных нет — нужен субмаксимальный тест (DDX или аналог); Apple Watch ±15% погрешность
- Текущий приоритет: выйти на стабильные 150 мин/нед Zone 2 → затем добавить 1 интервальную
