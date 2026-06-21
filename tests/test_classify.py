"""End-to-end regression harness for the write/role decision in bot.py.

Covers the behavior-audit-2026-06-21 probe set, but at the EFFECTIVE level:
the real runtime writes a fact via append_log_entry's classify_entry AND via
the food_like_message fallback in handle_message. This harness reproduces that
combined decision (no real log file is touched — it is computed, not written),
so it cannot give a false green like a classify_entry-only check would.

  A. must NOT write a fact (effective fact == "none")
  B. must write the right fact (weight / training / ...)
  C. write <-> role consistency (setback: no meal, role behaviorist)
  MIXED. opinion + a real meal report still logs the meal
  intent-7. detect_intent roles unchanged
  P4. pure question/planning is not appended to daily notes (in-memory)

Run: python3 tests/test_classify.py   (exit 0 = all pass)
"""
import sys
from pathlib import Path

HEALTH_OS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HEALTH_OS))

import bot  # noqa: E402


def effective_decision(msg: str) -> tuple[str, str]:
    """Reproduce the runtime write decision (classify_entry + food_like_message
    fallback from handle_message) without writing to a log. Returns (fact, role)
    where fact is one of weight/sleep/training/meal/none."""
    role = bot.detect_intent(msg)
    entry_type = bot.classify_entry(msg)
    food_like = (
        (role == "meal" or bot.is_food_message(msg))
        and role != "behaviorist"
        and not bot.is_planning_or_advice_query(msg)
        and not bot.is_question_message(msg)
        and not bot.is_decision_or_planning_question(msg)
    )
    if entry_type in ("weight", "sleep", "training", "meal"):
        fact = entry_type
    elif food_like:
        fact = "meal"
    else:
        fact = "none"
    return fact, role


def notes_count_after_append(msg: str) -> int:
    """P4: call append_log_entry with in-memory log IO; return notes appended."""
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


# (section, message, expected_fact, expected_role | None)
EFFECTIVE_CASES = [
    # A — must not write a fact
    ("A no-write", "хочу скинуть вес к лету", "none", None),
    ("A no-write", "вес встал колом, не падает", "none", None),
    ("A no-write", "сон у меня плохой последнее время", "none", None),
    ("A no-write", "хочу наладить сон", "none", None),
    ("A no-write", "люблю омлет по утрам", "none", "general"),
    ("A no-write", "какой омлет приготовить?", "none", "general"),
    ("A no-write", "расскажи про белок", "none", "general"),
    # B — must write the right fact
    ("B write-fact", "встал на весы — 82", "weight", None),
    ("B write-fact", "сегодня 82 кг утром", "weight", None),
    ("B write-fact", "пробежал 5 км утром", "training", None),
    # C — write must agree with role (setback: no meal, behaviorist)
    ("C role<->write", "сорвался, съел омлет вечером", "none", "behaviorist"),
    # MIXED — opinion + a real meal report still logs the meal
    ("MIXED", "съел омлет, люблю его", "meal", "meal"),
    ("MIXED", "на обед был омлет", "meal", "meal"),
    # ADVERSARIAL — false positives a probe-only set missed (gate review)
    ("ADVERSARIAL", "день прошёл нормально", "none", None),
    ("ADVERSARIAL", "прошёл собеседование сегодня", "none", None),
    ("ADVERSARIAL", "прошёл мимо зала, не зашёл", "none", None),
    ("ADVERSARIAL", "как прошёл день", "none", None),
    ("ADVERSARIAL", "пожал 80 кг утром", "training", None),
    ("ADVERSARIAL", "сейчас поем омлет", "none", "general"),
    ("ADVERSARIAL", "буду есть омлет", "none", "general"),
    # CONTROL — must keep working after the adversarial fixes
    ("CONTROL", "пробежал 5 км", "training", None),
    ("CONTROL", "прошёл 6 км", "training", None),
    ("CONTROL", "съел омлет, люблю его", "meal", "meal"),
    ("CONTROL", "сегодня 82 кг утром", "weight", None),
]

# intent-7 — role routing must not regress (detect_intent)
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


def main() -> int:
    rows = []  # (section, msg, expected, actual, ok)

    for sec, msg, exp_fact, exp_role in EFFECTIVE_CASES:
        fact, role = effective_decision(msg)
        if exp_role is None:
            exp, act, ok = f"fact={exp_fact}", f"fact={fact}", fact == exp_fact
        else:
            exp = f"{exp_fact}/{exp_role}"
            act = f"{fact}/{role}"
            ok = fact == exp_fact and role == exp_role
        rows.append((sec, msg, exp, act, ok))

    for msg, exp in INTENT_CASES:
        role = bot.detect_intent(msg)
        rows.append(("intent-7", msg, f"role={exp}", f"role={role}", role == exp))

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
