# Knowledge Base — Health OS

`knowledge/` — библиотека справочных протоколов. Бот не грузит ее целиком: в runtime всегда попадают только базовые файлы из `data/` и, при совпадении темы сообщения, одна или несколько нужных папок из `knowledge/`.

## Runtime

Бот всегда читает:

- `CLAUDE.md`
- `data/strategic/directives.yaml`
- `data/strategic/biomarkers.yaml`
- `data/tactical/user_profile.yaml`
- `data/tactical/strategy.md`
- `data/tactical/training/program.yaml`
- `data/tactical/nutrition/meals.yaml`
- `data/tactical/logs/YYYY-MM-DD.yaml` за сегодня

Бот не читает автоматически:

- весь `knowledge/`
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
