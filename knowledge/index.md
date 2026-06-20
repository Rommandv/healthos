# Knowledge Base — Health OS

`knowledge/` — библиотека справочных протоколов. Бот не грузит ее целиком: в runtime всегда попадают только базовые файлы из `data/` и, при совпадении темы сообщения, одна или несколько нужных папок из `knowledge/`.

## Runtime

Роль Coach задаётся встроенной инструкцией `RUNTIME_CONTEXT_INSTRUCTIONS` в `bot.py`, а не файлом `CLAUDE.md` — в runtime `CLAUDE.md` НЕ загружается.

Файлы из `data/` подгружаются **по интенту** сообщения (`context_files_for_intent` в `bot.py`), не все сразу:

| Интент | Контекст-файлы из `data/` | Лог дня |
|---|---|---|
| `meal` | directives, user_profile, strategy, nutrition/meals | да |
| `training` | directives, user_profile, strategy, training/program | да |
| `sleep_recovery` | directives, user_profile, strategy, training/program | да |
| `biomarkers_imaging` | directives, user_profile, biomarkers | нет |
| `behaviorist` | directives, user_profile, strategy, training/program | нет |
| `general` (по умолчанию) | directives, user_profile, strategy | да |

- `directives.yaml` и `user_profile.yaml` подгружаются при любом интенте.
- `biomarkers.yaml` — только при `biomarkers_imaging`.
- Лог дня (`data/tactical/logs/YYYY-MM-DD.yaml` за сегодня) — только для `meal / training / sleep_recovery / general` (`should_include_daily_log`).

Бот не читает автоматически:

- `CLAUDE.md` (роль зашита в `bot.py`)
- весь `knowledge/` целиком
- `knowledge/raw/**`
- `knowledge/sources/**`
- `knowledge/conflicts/**`
- любые `principles`-файлы

## Тематические папки

| Папка | Когда читать | Файлы |
|---|---|---|
| `sleep/` | сон, sleep, бессонница, проснулся, лег, выспался | `huberman_sleep.md` |
| `caffeine/` | кофе, caffeine, стимуляторы, фокус | `huberman_caffeine_focus.md` |
| `cardio/` | Zone 2, cardio, VO2, выносливость | `huberman_zone2_vo2max.md`, `vo2max_intervals_4x4_8x2.md` |
| `recovery/` | сауна, баня, восстановление, стресс, NSDR | `heat_sauna_recovery.md`, `recovery_stress_nsdr.md`, `huberman_dopamine_motivation.md` |
| `nutrition/` | еда, питание, белок, калории, meal | `nutrition_synth_playbook.md`, `meal_timing_by_training.md` |
| `biomarkers/` | анализы, ApoB, LDL, HDL, HbA1c, инсулин | `attia_lipids_apob_ldl.md` |
| `training/` | тренировка, упражнения, мышцы, силовая | `levin_exercise_longevity.md` |
| `conflicts/` | ручная проверка конфликтов между источниками | `expert_conflicts.md` |
| `sources/` | ручная проверка источников для синтезов | `sources_*.md` |
| `raw/` | сырые транскрипты и сборочные материалы | не читается автоматически |

## Структура

```text
knowledge/
├── index.md
├── sleep/
├── caffeine/
├── cardio/
├── recovery/
├── nutrition/
├── biomarkers/
├── training/
├── conflicts/
├── sources/
└── raw/
```
