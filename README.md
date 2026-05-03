# Health OS Telegram Bot

Минимальный Telegram-бот для персональной Health OS. Он пишет дневные факты в YAML-лог, читает фиксированный runtime-контекст из `data/` и подтягивает тематические протоколы из `knowledge/` только по ситуации, а затем отвечает как health-coach через Anthropic.

## Run

```bash
cp .env.example .env
python3 -m pip install -r requirements.txt
python3 bot.py --check
python3 bot.py
```

Для polling нужен `TELEGRAM_BOT_TOKEN` в `.env`. Без `ANTHROPIC_API_KEY` бот всё равно логирует сообщения, но не вызывает Anthropic.

## Structure

```text
data/
  strategic/
    directives.yaml      # долгосрочные ограничения и приоритеты
    biomarkers.yaml      # анализы и измерения
    goals.md             # долгосрочные цели
  tactical/
    user_profile.yaml    # профиль пользователя
    strategy.md          # текущая тактическая стратегия
    logs/                # дневные логи YYYY-MM-DD.yaml
    training/
      program.yaml       # программа тренировок
    nutrition/
      meals.yaml         # шаблоны еды и тайминг
knowledge/
  index.md               # карта библиотеки знаний
  sleep/                 # сон
  caffeine/              # кофеин и фокус
  cardio/                # Zone 2, VO2max, выносливость
  recovery/              # восстановление, стресс, NSDR, сауна
  nutrition/             # питание, белок, калории, meal timing
  biomarkers/            # анализы, липиды, ApoB/LDL/HDL/HbA1c
  training/              # силовые, мышцы, longevity
  sources/               # источники для ручной проверки
  conflicts/             # конфликты между источниками
  raw/                   # сырые транскрипты и сборочные материалы, ботом не читаются
docs/
  setup-guide.md         # установочный гайд, не runtime-контекст
bot.py                   # Telegram entrypoint
```

## Source Of Truth

- `CLAUDE.md` — главный системный протокол Health OS: роли, иерархия решений, правила Coach/Strategist/CMO/Analyst/Behaviorist.
- Runtime-контекст бота — только `CLAUDE.md`, фиксированные файлы из `data/strategic/` и `data/tactical/`, текущая программа/питание и сегодняшний дневной лог.
- `data/strategic/directives.yaml` важнее тактических предпочтений.
- `data/tactical/user_profile.yaml` нужен для расчета калорий, макросов и тренировочной нагрузки.
- `data/tactical/training/program.yaml` является текущим источником плана тренировок.
- `data/tactical/logs/YYYY-MM-DD.yaml` хранит факт дня: еда, тренировки, сон, вес, заметки.
- `knowledge/` — библиотека знаний. Бот выбирает нужную тематическую папку по тексту сообщения: сон, кофеин, кардио, восстановление, питание, биомаркеры или тренировки.
- `knowledge/raw/**`, `knowledge/sources/**`, `knowledge/conflicts/**` и любые `principles`-файлы не передаются в обычный runtime-контекст автоматически.
- `docs/setup-guide.md` — установочный гайд. Он не входит в постоянный runtime-контекст и нужен только при настройке/онбординге.

## Daily Log Template

```yaml
date: YYYY-MM-DD
weight_morning: null

meals:
  - time: null
    description: null
    calories: null
    protein_g: null
    notes: null

training:
  - type: null
    name: null
    duration_min: null
    rpe: null
    exercises: []

sleep:
  hours: null
  quality: null
  bed_time: null
  wake_time: null

recovery:
  nsdr_min: null
  stress: null

notes: null
```

## Next Step

Заполнить `data/tactical/user_profile.yaml`. После этого можно рассчитать стартовые калории, белок и уточнить программу под доступ к залу, ограничения и расписание.
