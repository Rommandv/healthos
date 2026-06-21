"""Regression harness for the write/role decision in bot.py.

Covers the behavior-audit-2026-06-21 probe set:
  A. must NOT write a fact (classify_entry -> "note")
  B. must write the right fact (classify_entry -> weight/training/...)
  C. write <-> role consistency (setback: no silent meal; role=behaviorist)
  P4. pure question/planning is not appended to daily notes
Plus the 7 intent-routing cases from the previous regression (detect_intent).

Treats classify_entry / detect_intent / append_log_entry as black boxes
(no new helper names referenced), so the same file runs both at BASELINE
and after the P1-P4 fixes. No real log files are touched: append_log_entry's
IO is monkeypatched to an in-memory dict.

Run: python3 tests/test_classify.py   (exit 0 = all pass)
"""
import sys
from pathlib import Path

HEALTH_OS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HEALTH_OS))

import bot  # noqa: E402

# A — false-positive writes: intention / opinion / question / complaint -> note
A_CASES = [
    "хочу скинуть вес к лету",
    "вес встал колом, не падает",
    "сон у меня плохой последнее время",
    "хочу наладить сон",
    "люблю омлет по утрам",
    "какой омлет приготовить?",
    "расскажи про белок",
]

# B — missed real facts
B_CASES = [
    ("встал на весы — 82", "weight"),
    ("сегодня 82 кг утром", "weight"),
    ("пробежал 5 км утром", "training"),
]

# C — write must agree with role: setback should not silently log a meal
C_CASES = [
    ("сорвался, съел омлет вечером", "note", "behaviorist"),
]

# intent-7 — previous detect_intent regression must not change
INTENT_CASES = [
    ("сорвался вечером, сожрал пол-холодильника", "behaviorist"),
    ("думаю съесть побольше белка, стоит ли?", "general"),
    ("утром 3 яйца, тост и авокадо", "meal"),
    ("присед 100 кг 5х5, как прогрессия?", "training"),
    ("спал 5 часов, разбитый", "sleep_recovery"),
    ("сдал анализы: ApoB 80, LDL 3.1", "biomarkers_imaging"),
    ("стоит ли сейчас уходить в дефицит или держать поддержку?", "general"),
]

# P4 — pure question/planning must NOT land in daily notes; real note still does
P4_CASES = [
    ("стоит ли уходить в дефицит или держать поддержку?", 0),
    ("как лучше восстановиться после недосыпа?", 0),
    ("болит плечо", 1),  # control: a genuine note is still logged
]


def notes_count_after_append(msg: str) -> int:
    """Call append_log_entry with in-memory log IO; return notes appended."""
    orig_read, orig_write = bot.read_daily_log, bot.write_daily_log
    bot.read_daily_log = lambda: {
        "date": "test", "weight_morning": None, "sleep": {},
        "meals": [], "training": [], "notes": [], "active_training": None,
    }
    bot.write_daily_log = lambda dl: None
    try:
        _type, dl = bot.append_log_entry(msg, "tester")
        return len(dl.get("notes", []))
    finally:
        bot.read_daily_log, bot.write_daily_log = orig_read, orig_write


def main() -> int:
    rows = []  # (section, msg, expected, actual, ok)

    for msg in A_CASES:
        actual = bot.classify_entry(msg)
        rows.append(("A no-write", msg, "note", actual, actual == "note"))

    for msg, exp in B_CASES:
        actual = bot.classify_entry(msg)
        rows.append(("B write-fact", msg, exp, actual, actual == exp))

    for msg, exp_cls, exp_role in C_CASES:
        cls = bot.classify_entry(msg)
        role = bot.detect_intent(msg)
        rows.append((
            "C role<->write", msg, f"{exp_cls}+{exp_role}",
            f"{cls}+{role}", cls == exp_cls and role == exp_role,
        ))

    for msg, exp in INTENT_CASES:
        actual = bot.detect_intent(msg)
        rows.append(("intent-7", msg, exp, actual, actual == exp))

    for msg, exp in P4_CASES:
        n = notes_count_after_append(msg)
        rows.append(("P4 no-note", msg, f"notes={exp}", f"notes={n}", n == exp))

    width = max(len(m) for _, m, *_ in rows)
    print(f"{'SECTION':<14} | {'MESSAGE':<{width}} | {'EXPECT':<16} | {'ACTUAL':<16} | R")
    print("-" * (14 + width + 44))
    for sec, msg, exp, act, ok in rows:
        print(f"{sec:<14} | {msg:<{width}} | {exp:<16} | {act:<16} | {'PASS' if ok else 'FAIL'}")

    passed = sum(1 for *_, ok in rows if ok)
    total = len(rows)
    print(f"\nSUMMARY: {passed}/{total} PASS, {total - passed} FAIL")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
