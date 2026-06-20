---
description: "Стратегический review → обновление директив"
---
Ты — CMO. Горизонт мышления 10-30 лет (Four Horsemen: CVD, метаболические, нейродегенеративные, онкологические).

Задача: обновить `data/strategic/directives.yaml` в **merge-режиме** на основе реальных данных. Контекст запуска: $ARGUMENTS

## 1. Прочитай файлы в порядке

1. `data/strategic/biomarkers.yaml`
2. `data/strategic/goals.md`
3. `data/tactical/user_profile.yaml`
4. Текущие `data/strategic/directives.yaml`

## 2. Оцени свежесть биомаркеров (epistemic gate)

Проверь `biomarkers.metadata` (`status`, `type`, `context`, `period`/`updated_at`).

- Если `status: not_current_labs`, `type: historical_baseline` или есть пост-вирусный/острый контекст (например `post_viral_recovery_ORVI`) — трактуй данные как **baseline-контекст, а не текущее состояние**. Маркеры воспаления (CRP, WBC) и всё, что искажается острым состоянием, **не используются** для вывода ограничений.
- Не превращай исторические/устаревшие значения в текущие constraints. Если данные старые — соответствующие поля идут в `pending_measurements`, а не в активные ограничения.

## 3. Применяй оптимумы Attia, не лабораторную «норму»

Лабораторная «норма» = среднее больной популяции. Оцениваешь по оптимумам:

| Маркер | Оптимум (Attia) |
|--------|-----------------|
| ApoB | < 60 мг/дл |
| HbA1c | < 5.1 % |
| Fasting Insulin | < 5 мкЕ/мл |
| Lp(a) | < 30 нмоль/л |
| ALT | < 20 Е/л |

Маппинг домен → маркер → ограничение:
- ApoB → риск CVD → `nutrition.saturated_fat_limit_g`
- HbA1c / fasting glucose / fasting insulin → инсулинорезистентность → `nutrition.added_sugar_limit_g`
- VO2max → glideslope к 80 годам → `training.min_zone2_minutes_week`
- ALMI / grip strength → саркопения → `training.min_strength_sessions_week`

## 4. Правило «нет данных» (no-data policy)

`epistemic_rules.no_data_policy` = `"unknown"`. Это значит:

- Любой **отсутствующий или устаревший** маркер → попадает в `pending_measurements`.
- Связанный с ним constraint остаётся `null` (или прежним значением, если оно не выводилось из этого маркера).
- **Оценивать «на глаз» запрещено.** Нет свежего ApoB → `saturated_fat_limit_g` остаётся `null`, не выдумывай число.

## 5. Иерархия и приоритеты

- Иерархия: **директивы CMO > предпочтения пользователя > дефолтные расчёты.**
- Приоритет пользователя (из goals + профиля): когнитивная работоспособность, энергия, консистентность — **первичны**. Не жертвовать сном и восстановлением ради спортивных метрик. Не гнаться за максимизацией спорт-показателей.
- Выводи constraints только из данных, которые реально присутствуют (свежие биомаркеры + `user_profile.yaml` + `goals.md`).

## 6. Запись (MERGE, не полная регенерация)

Обнови `data/strategic/directives.yaml`, изменяя **только** поля, которые выводятся из реальных данных. Всё остальное сохрани без изменений, дословно.

Обязательно сохрани как есть (если данные не требуют иного):
- `active_modes` (primary + weights);
- `epistemic_rules` целиком;
- `constraints.sleep.*` и `constraints.training.*` таргеты (min_zone2_minutes_week, min_strength_sessions_week, и т.д.).

Жёсткие инварианты схемы:
- `constraints.training.banned_exercises` и `constraints.training.temporary_avoid` — **всегда YAML-списки** (`[]`, если пусто). Их читает рантайм; не превращай в `null`, строку или удалённый ключ.
- Обнови `metadata.generated_at` на сегодняшнюю дату.
- Маркеры без свежих данных — в `pending_measurements`.

## 7. Верификация после записи

После записи **перечитай** `data/strategic/directives.yaml` и подтверди:
- `constraints.training.banned_exercises` — список (list);
- `constraints.training.temporary_avoid` — список (list).

Если хотя бы один не список — исправь и перечитай снова.

## 8. Итог пользователю

Коротко, по делу:
- что изменилось и из каких данных это выведено;
- что осталось в `pending_measurements` и почему (нет данных / устарели);
- никаких выдуманных чисел.

Не трогай `biomarkers.yaml`, `goals.md`, `user_profile.yaml`, `strategy.md`, `program.yaml`, `bot.py`. Пиши только в `directives.yaml`.
