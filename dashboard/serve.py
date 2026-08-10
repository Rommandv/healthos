#!/usr/bin/env python3
"""Фундамент — локальный read-only дашборд Health OS.

Читает YAML из data/ на каждый запрос (живое обновление без перезапуска),
отдаёт агрегированное состояние на /api/state и статический index.html.

Запуск: python dashboard/serve.py  →  http://localhost:8787
Ничего не пишет: ни в data/, ни куда-либо ещё.
"""

import json
import re
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DASHBOARD = Path(__file__).resolve().parent
PORT = 8787

# --- загрузка -----------------------------------------------------------


def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}


def load_logs():
    """date -> лог дня. Дата берётся из имени файла YYYY-MM-DD.yaml."""
    logs = {}
    logs_dir = DATA / "tactical" / "logs"
    if not logs_dir.is_dir():
        return logs
    for p in sorted(logs_dir.glob("*.yaml")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", p.stem)
        if not m:
            continue
        try:
            d = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        log = load_yaml(p)
        if log:
            logs[d] = log
    return logs


# --- помощники: no_data_policy = None, никаких догадок --------------------


def as_number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def dig(mapping, *keys):
    cur = mapping
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def first_number(log, *paths):
    """Первое числовое значение по списку путей (поддержка альтернативных мест поля)."""
    for path in paths:
        v = as_number(dig(log, *path))
        if v is not None:
            return v
    return None


# --- извлечение метрик из лога дня ---------------------------------------

STRENGTH_TYPES = {"strength", "strength_cardio"}
ZONE2_TYPES = {"zone2", "cardio"}


def sleep_hours(log):
    return first_number(log, ("sleep", "hours"), ("sleep_hours",))


def sleep_bed_time(log):
    v = dig(log, "sleep", "bed_time") or log.get("bed_time")
    return v if isinstance(v, str) and re.match(r"^\d{1,2}:\d{2}$", v) else None


def trainings(log):
    t = log.get("training")
    return [e for e in t if isinstance(e, dict)] if isinstance(t, list) else []


def is_strength(entry):
    return entry.get("type") in STRENGTH_TYPES


def zone2_minutes(entry):
    if entry.get("type") in ZONE2_TYPES or entry.get("zone") == 2:
        return as_number(entry.get("duration_min")) or as_number(entry.get("minutes")) or 0
    return 0


def day_protein(log):
    meals = log.get("meals")
    if not isinstance(meals, list):
        return None
    values = [as_number(m.get("protein_g")) for m in meals if isinstance(m, dict)]
    values = [v for v in values if v is not None]
    return round(sum(values), 1) if values else None


def day_fiber(log):
    total = first_number(log, ("nutrition", "fiber_g"), ("fiber_g",))
    if total is not None:
        return total
    meals = log.get("meals")
    if not isinstance(meals, list):
        return None
    values = [as_number(m.get("fiber_g")) for m in meals if isinstance(m, dict)]
    values = [v for v in values if v is not None]
    return round(sum(values), 1) if values else None


def day_energy(log):
    return first_number(log, ("energy_1_10",), ("recovery", "energy_1_10"))


def day_rhr(log):
    return first_number(log, ("rhr",), ("recovery", "rhr"))


def day_hrv(log):
    return first_number(log, ("hrv",), ("recovery", "hrv"))


# --- агрегация ------------------------------------------------------------


def parse_protein_rule(rule, weight_kg):
    """'1.6-2.2 g/kg/day' × вес → диапазон в граммах; без веса — None."""
    if not isinstance(rule, str) or not as_number(weight_kg):
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", rule)
    if len(nums) < 2:
        return None
    lo, hi = float(nums[0]), float(nums[1])
    return {"min_g": round(lo * weight_kg), "max_g": round(hi * weight_kg), "rule": rule}


def build_verdict(today_log, today_sleep, sleep_c):
    if today_log is None:
        return {"text": "Сегодня ещё не залогировано", "tone": "muted"}
    if today_sleep is None:
        return {"text": "Сон сегодня не залогирован", "tone": "muted"}
    t_min = as_number(sleep_c.get("target_hours_min"))
    if today_sleep < 6:
        return {"text": "Просел сон — сегодня Zone 1 или отдых", "tone": "warn"}
    if t_min is not None and today_sleep < t_min:
        return {"text": "Сон ниже цели — без тяжёлой нагрузки", "tone": "warn"}
    return {"text": "Фундамент держится", "tone": "ok"}


def sleep_status(hours, sleep_c):
    if hours is None:
        return "нет данных"
    if hours < 6:
        return "просел"
    t_min = as_number(sleep_c.get("target_hours_min"))
    if t_min is not None and hours < t_min:
        return "ниже цели"
    return "в коридоре"


def week_start(d):
    return d - timedelta(days=d.weekday())


def build_state():
    directives = load_yaml(DATA / "strategic" / "directives.yaml")
    biomarkers = load_yaml(DATA / "strategic" / "biomarkers.yaml")
    profile = load_yaml(DATA / "tactical" / "user_profile.yaml")
    logs = load_logs()

    today = date.today()
    today_log = logs.get(today)

    constraints = directives.get("constraints") or {}
    sleep_c = constraints.get("sleep") or {}
    training_c = constraints.get("training") or {}
    nutrition_c = constraints.get("nutrition") or {}

    # --- сон: сегодня + 7 дней
    today_sleep = sleep_hours(today_log) if today_log else None
    sleep_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        log = logs.get(d)
        sleep_days.append({
            "date": d.isoformat(),
            "hours": sleep_hours(log) if log else None,
        })

    # --- движение: текущая неделя + 4 недели истории
    this_week = week_start(today)
    weeks = []
    for w in range(3, -1, -1):
        ws = this_week - timedelta(weeks=w)
        strength_days = set()
        z2 = 0
        for d, log in logs.items():
            if ws <= d < ws + timedelta(days=7):
                for e in trainings(log):
                    if is_strength(e):
                        strength_days.add(d)
                    z2 += zone2_minutes(e)
        weeks.append({
            "label": f"{ws.day:02d}.{ws.month:02d}",
            "current": ws == this_week,
            "strength_sessions": len(strength_days),
            "zone2_min": round(z2),
        })

    # --- питание: последние 7 дней, только залогированные
    weight_kg = as_number(dig(profile, "identity", "weight_kg"))
    protein_target = parse_protein_rule(nutrition_c.get("protein_rule"), weight_kg)
    nutrition_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        log = logs.get(d)
        if not log:
            continue
        protein = day_protein(log)
        fiber = day_fiber(log)
        if protein is None and fiber is None:
            continue
        nutrition_days.append({"date": d.isoformat(), "protein_g": protein, "fiber_g": fiber})

    # --- нервная система: последние 7 дней
    nervous_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        log = logs.get(d)
        if not log:
            continue
        energy, rhr, hrv = day_energy(log), day_rhr(log), day_hrv(log)
        if energy is None and rhr is None and hrv is None:
            continue
        nervous_days.append({"date": d.isoformat(), "energy": energy, "rhr": rhr, "hrv": hrv})

    # --- месяц: покрытие + 30-дневные ряды
    month_days = []
    d = today.replace(day=1)
    while d.month == today.month:
        month_days.append({
            "day": d.day,
            "logged": d in logs,
            "future": d > today,
            "today": d == today,
        })
        d += timedelta(days=1)

    series_30 = {"sleep": [], "training_min": []}
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        log = logs.get(d)
        series_30["sleep"].append(sleep_hours(log) if log else None)
        if log:
            total = sum(
                as_number(e.get("duration_min")) or as_number(e.get("minutes")) or 0
                for e in trainings(log)
            )
            series_30["training_min"].append(round(total) if total else None)
        else:
            series_30["training_min"].append(None)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "today_human": f"{today.day} {MONTHS_RU[today.month]} {today.year}",
        "verdict": build_verdict(today_log, today_sleep, sleep_c),
        "sleep": {
            "today": {
                "hours": today_sleep,
                "bed_time": sleep_bed_time(today_log) if today_log else None,
                "status": sleep_status(today_sleep, sleep_c) if today_log else "нет данных",
            },
            "target": {
                "hours_min": as_number(sleep_c.get("target_hours_min")),
                "hours_max": as_number(sleep_c.get("target_hours_max")),
                "bed_time": sleep_c.get("target_bed_time"),
                "wake_time": sleep_c.get("target_wake_time"),
            },
            "days": sleep_days,
        },
        "movement": {
            "week": {
                "strength_sessions": weeks[-1]["strength_sessions"],
                "strength_target": as_number(training_c.get("min_strength_sessions_week")),
                "zone2_min": weeks[-1]["zone2_min"],
                "zone2_target": as_number(training_c.get("min_zone2_minutes_week")),
            },
            "weeks": weeks,
        },
        "nutrition": {
            "protein_target": protein_target,
            "fiber_min_g": as_number(nutrition_c.get("fiber_minimum_g")),
            "weight_kg": weight_kg,
            "days": nutrition_days,
        },
        "nervous": {
            "days": nervous_days,
            "source_hint": "Данные появятся из утреннего чек-ина боту: энергия 1–10, пульс покоя (rhr), HRV.",
        },
        "month": {
            "label": f"{MONTHS_RU_NOM[today.month]} {today.year}",
            "days": month_days,
            "logged_count": sum(1 for x in month_days if x["logged"]),
            "series_30": series_30,
        },
        "labs": build_labs(biomarkers, directives),
        "directives": build_directives_summary(directives),
    }


MONTHS_RU = {1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
             7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"}
MONTHS_RU_NOM = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
                 7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}

PANEL_LABELS = [
    ("biochemistry", "Биохимия крови"),
    ("cbc", "Общий анализ крови"),
    ("hormones", "Гормоны"),
    ("inbody", "InBody · состав тела"),
    ("cardiac_imaging", "ЭхоКГ"),
]

MARKER_LABELS = {
    "glucose": "Глюкоза", "total_cholesterol": "Общий холестерин", "LDL": "ЛПНП (LDL)",
    "ALT": "АЛТ", "AST": "АСТ", "creatinine": "Креатинин", "CRP": "СРБ (CRP)", "LDH": "ЛДГ",
    "WBC": "Лейкоциты", "RBC": "Эритроциты", "HGB": "Гемоглобин", "HCT": "Гематокрит",
    "PLT": "Тромбоциты", "neutrophils": "Нейтрофилы", "lymphocytes": "Лимфоциты", "ESR": "СОЭ",
    "TSH": "ТТГ", "weight": "Вес", "PBF": "Жир (PBF)", "SMM": "Мышечная масса",
    "visceral_fat": "Висцеральный жир", "BMR": "BMR", "phase_angle": "Фазовый угол",
}

WARN_INTERPRETATIONS = ("above", "elevated", "high", "low_")


def panel_label_and_date(key):
    label = None
    for prefix, ru in PANEL_LABELS:
        if key.startswith(prefix):
            label = ru
            break
    if label is None:
        label = key.replace("_", " ")
    m = re.search(r"(\d{4})_(\d{2})(?:_(\d{2}))?", key)
    date_label = None
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12:
            date_label = f"{MONTHS_RU_NOM[month].lower()} {year}"
    return label, date_label


def marker_flag(info):
    interp = info.get("interpretation")
    if isinstance(interp, str) and any(w in interp for w in WARN_INTERPRETATIONS):
        return "warn"
    return None


def build_labs(biomarkers, directives):
    current_panels, historical_panels, imaging = [], [], []

    for key, block in biomarkers.items():
        if not isinstance(block, dict) or "status" not in block:
            continue
        label, date_label = panel_label_and_date(key)
        status = block.get("status")

        if block.get("type") == "echocardiography" or key.startswith("cardiac_imaging"):
            ef = dig(block, "left_ventricle", "ejection_fraction_percent")
            conclusion = block.get("conclusion") if isinstance(block.get("conclusion"), list) else []
            imaging.append({
                "label": "ЭхоКГ",
                "date": str(block.get("date") or date_label or ""),
                "status": status,
                "highlights": ([f"ФВ {ef}%"] if as_number(ef) else []),
                "conclusion": [str(c) for c in conclusion],
            })
            continue

        markers = []
        for name, info in block.items():
            if not isinstance(info, dict) or "value" not in info:
                continue
            markers.append({
                "name": MARKER_LABELS.get(name, name),
                "value": info.get("value"),
                "unit": str(info.get("unit") or ""),
                "flag": marker_flag(info),
                "target": info.get("target"),
            })
        if not markers:
            continue
        panel = {"label": label, "date": date_label, "markers": markers}
        (current_panels if status == "current" else historical_panels).append(panel)

    # ЭКГ: записи в системе нет — честная строка «нет данных»
    if not any("ЭКГ" == im["label"] for im in imaging):
        imaging.append({"label": "ЭКГ", "date": None, "status": None,
                        "highlights": [], "conclusion": []})

    # контекст historical-панелей из notes
    historical_note = None
    for note in (dig(biomarkers, "metadata", "notes") or []):
        if isinstance(note, str) and "ORVI" in note:
            historical_note = ("Панели сент–окт 2025 сданы в период восстановления после ОРВИ — "
                               "CRP и лейкоциты могут отражать временное воспаление.")
            break

    # «Сдать далее»
    retest = []
    for p in historical_panels:
        when = f" — последняя сдача: {p['date']}" if p["date"] else ""
        retest.append({"title": f"Пересдать: {p['label']}{when}", "reason": "панель устарела (historical)"})

    pending = directives.get("pending_measurements")
    if isinstance(pending, list) and pending:
        retest.append({
            "title": "Ждут первого измерения: " + ", ".join(str(x) for x in pending),
            "reason": "pending_measurements в директивах",
        })

    nutrition_c = dig(directives, "constraints", "nutrition") or {}
    null_constraints = [k for k, v in nutrition_c.items() if v is None]
    if null_constraints:
        retest.append({
            "title": "Лимиты по питанию не заданы: " + ", ".join(null_constraints),
            "reason": "ждут свежей липидной панели и метаболических маркеров",
        })

    return {
        "current": current_panels,
        "historical": historical_panels,
        "historical_note": historical_note,
        "imaging": imaging,
        "retest": retest,
    }


def build_directives_summary(directives):
    constraints = directives.get("constraints") or {}
    modes = directives.get("active_modes") or {}
    weights = modes.get("weights") or {}
    return {
        "generated_at": str(dig(directives, "metadata", "generated_at") or ""),
        "primary_mode": modes.get("primary"),
        "weights": {str(k): v for k, v in weights.items() if as_number(v) is not None},
        "sleep": constraints.get("sleep") or {},
        "training": constraints.get("training") or {},
        "nutrition": {k: v for k, v in (constraints.get("nutrition") or {}).items() if v is not None},
        "recovery": constraints.get("recovery") or {},
        "no_data_policy": dig(directives, "epistemic_rules", "note"),
    }


# --- сервер ---------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/api/state":
            try:
                body = json.dumps(build_state(), ensure_ascii=False).encode("utf-8")
                self._send(200, "application/json; charset=utf-8", body)
            except Exception as e:  # не роняем сервер из-за битого YAML
                err = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
                self._send(500, "application/json; charset=utf-8", err)
        elif self.path.split("?")[0] in ("/", "/index.html"):
            try:
                body = (DASHBOARD / "index.html").read_bytes()
                self._send(200, "text/html; charset=utf-8", body)
            except OSError:
                self._send(404, "text/plain; charset=utf-8", b"index.html not found")
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    def _send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # тихий сервер


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Фундамент → http://localhost:{PORT}  (Ctrl+C для остановки)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")


if __name__ == "__main__":
    main()
