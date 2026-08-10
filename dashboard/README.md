# Фундамент — read-only дашборд Health OS

Локальная страница «зашёл и за 10 секунд понял, что с фундаментом»: сон, движение,
питание, нервная система, покрытие месяца, анализы и действующие директивы.

## Запуск

```bash
cd ~/Documents/VibeCoding/projects/health-os
python3 dashboard/serve.py
# → http://localhost:8787
```

Зависимости: только PyYAML (уже в `requirements.txt`). Сервер — stdlib `http.server`.

## Принципы

- **Read-only.** Дашборд ничего не пишет — ни в `data/`, ни куда-либо ещё.
  Весь ввод данных остаётся за ботом и slash-командами (`/health-labs`, `/health-daily`).
- **Живое чтение.** YAML читается заново на каждый запрос: поменял файл → обновил
  страницу. Без пересборки и перезапуска.
- **no_data_policy.** Если метрика не измерена — показывается «нет данных».
  Никаких оценок на глаз и экстраполяций (правило из `directives.yaml`).
- **Цели не хардкодятся.** Коридор сна, минимумы силовых/Zone 2, клетчатка,
  правило белка — всё берётся из `data/strategic/directives.yaml`;
  вес — из `data/tactical/user_profile.yaml`.
- **Historical ≠ current.** Панели биомаркеров со `status: historical`
  (сент–окт 2025, пост-ОРВИ) показываются приглушённо и отдельно от действующих.

## Схема дневного лога, которую понимает дашборд

Файлы: `data/tactical/logs/YYYY-MM-DD.yaml` (дата берётся из имени файла).
Неизвестные поля игнорируются молча — боту можно писать что угодно сверх этого.

```yaml
date: '2026-07-06'
weight_morning: 74.0          # пока не отображается, зарезервировано

sleep:
  hours: 7.5                  # → столп «Сон», спарклайны, вердикт дня
  bed_time: '23:10'           # → сравнение с target_bed_time
  quality: good               # читается, пока не отображается
# альтернатива: sleep_hours / bed_time на верхнем уровне тоже понимаются

training:
  - type: strength            # strength | strength_cardio → счётчик силовых (день с ≥1 записью = 1 сессия)
    duration_min: 50          # → минуты тренировок за 30 дней
  - type: zone2               # zone2 | cardio (или zone: 2) → минуты Zone 2 за неделю
    duration_min: 35

meals:
  - protein_g: 42             # суммируется по дню → столп «Питание»
    fiber_g: 8                # суммируется по дню (или nutrition.fiber_g итогом за день)

energy_1_10: 7                # → «Нервная система» (или recovery.energy_1_10)
rhr: 52                       # пульс покоя, уд/мин (или recovery.rhr)
hrv: 68                       # мс (или recovery.hrv)
```

Минимум, чтобы дашборд «ожил»: `sleep.hours` каждый день. Остальное подтянется
по мере того, как бот начнёт писать `type`/`duration_min` у тренировок,
`protein_g` у еды и утренний чек-ин (`energy_1_10`, `rhr`, `hrv`).

## Что откуда читается

| Секция | Источник |
|---|---|
| Вердикт дня | сегодняшний лог + `recovery_rule` и коридор сна из directives |
| Столпы (4) | `data/tactical/logs/*.yaml` против целей из directives |
| Месяц | наличие лог-файлов по дням + 30-дневные ряды сна/тренировок |
| Анализы | `data/strategic/biomarkers.yaml` (per-dataset `status`) |
| Сдать далее | historical-панели + `pending_measurements` + null-констрейнты питания |
| Директивы | `data/strategic/directives.yaml` |

## Файлы

- `serve.py` — сервер и вся агрегация (YAML → JSON `/api/state`)
- `index.html` — вся вёрстка и рендер (vanilla JS, без сборки)
