# Sources — Lipids & Longevity

## Best for
LDL, ApoB, CRP, сердечно-сосудистый риск, долголетие, биомаркеры как цели, а не "норма".

**Tier 2:** Thomas Dayspring (липидология, ApoB как первичный маркер CVD-риска)
**Tier 3:** Attia (протоколы, backcasting), Gil Carvalho / Nutrition Made Simple (научный разбор)

При конфликте → Dayspring / AHA/ACC guidelines / Tier 1 RCT первичны.

---

## Protocols we use IN THIS Health OS

**biomarkers.yaml — текущие значения (Sept–Oct 2025):**
- LDL: 3.44 mmol/L → elevated по Attia (оптимум <2.6 / ApoB <60 мг/дл)
- CRP: 5.1 mg/L → elevated (норма <3.0; цель <1.0 по Attia); контекст: post-viral
- ApoB: ⚠️ данных нет → ПРИОРИТЕТ анализ до мая 2026
- HDL: ⚠️ данных нет → следующие анализы

**directives.yaml — выводы из биомаркеров:**
- `nutrition.saturated_fat_limit_g: 15` — прямое следствие LDL 3.44 + CRP 5.1
- `nutrition.omega3_minimum_g: 2` — anti-inflammatory (CRP), EPA+DHA; рыба или добавка
- Эти цифры менять только через `/health-strategy` + новые анализы

**Recovery Gate — связь с липидами:**
- Хроническое YELLOW/RED → хронический стресс → ↑CRP → ↑CVD-риск
- Поэтому Recovery Gate определяет режим, а не "хочу потренироваться"

**Analyst role — правило:**
- Биомаркеры сравнивать с оптимумами Attia/Dayspring, не с лабораторными "нормами"
- "Норма" = среднее больной популяции; наша цель — Attia optimum
- Изменения в directives.yaml — только после явного "да" пользователя

---

## Metrics to track (приоритет по времени)
1. ApoB — главный: ⚠️ до мая 2026
2. HDL — кардиориск вместе с ApoB: ⚠️ следующие анализы
3. HbA1c — гликемический контроль: ⚠️ следующие анализы
4. Insulin fasting (HOMA-IR): ⚠️ следующие анализы
5. Lp(a) — генетический риск, меняется редко: ⚠️ один раз
6. LDL повторно — после 3 мес. изменений в питании
7. CRP повторно — ожидаем снижение при нормализации (post-viral)

---

## Common misreads / what to ignore
- "LDL норма в лаборатории" — норма лаборатории это <5.0 mmol/L; Attia/Dayspring цель <2.6 (или ApoB <60)
- "Насыщенный жир повышает 'хороший' HDL" — частично верно, но ApoB при этом тоже растёт → net harm при высоком исходном LDL
- "Яйца можно есть без ограничений" — зависит от ApoB статуса; при elevated LDL — контролировать
- "CRP 5.1 — это высокий воспалительный маркер навсегда" — CRP реактивный; post-viral снижается; повторить через 3–6 мес

---

## Evidence notes
- Dayspring (Tier 2): ApoB — количество атерогенных частиц; первичен по сравнению с LDL-C
- AHA/ACC (Tier 1): при LDL ≥3.37 mmol/L и наличии риск-факторов → активное снижение
- CRP 5.1 (high-sensitivity): умеренно-высокий; снижение через омега-3 + Zone 2 + сон — протокол обоснован Tier 1
- Attia backcasting: цель — VO2max >95th percentile в 80 лет; каждый год без прогресса сужает окно
- Carvalho: sat fat → ↑LDL particle number (Tier 2/3 consensus) → поддерживает наш лимит 15г
