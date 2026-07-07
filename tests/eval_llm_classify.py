"""Eval for the LLM-primary classifier (prod path).

Runs the probe set through the REAL classifier `bot.shadow_classify()`, N times
each (temp 0; N runs surface flakiness), and scores against the expectations
mapped to the LLM output shape {intent, loggable, log_type}.

Prod has no regex guard anymore (pure-LLM switch), so this measures the LLM
alone — which IS the production behavior.

Mapping:
- don't-write cases (fact "none"): loggable=false, log_type=none.
- write cases (meal/weight/sleep/training): loggable=true + that log_type.
- intent checked only where meaningful: C (behaviorist), MIXED (meal), intent-7.
- P4 (questions / pain note): not a trackable fact -> loggable=false.

SAFETY set (must be 100%): A ("no-write") + C (no-write & behaviorist).
Non-safety set: >= 0.95.

Needs ANTHROPIC_API_KEY. Cost: (cases x N) Haiku calls. Does not modify bot.py.
Run: python3 tests/eval_llm_classify.py
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HEALTH_OS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HEALTH_OS))

import bot  # noqa: E402

N = int(os.getenv("EVAL_N", "5"))
WORKERS = int(os.getenv("EVAL_WORKERS", "3"))
SAFETY_SECTIONS = {"A no-write", "C role<->write"}

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
    # ADVERSARIAL — false positives a probe-only set missed
    ("ADVERSARIAL", "день прошёл нормально", "none", None),
    ("ADVERSARIAL", "прошёл собеседование сегодня", "none", None),
    ("ADVERSARIAL", "прошёл мимо зала, не зашёл", "none", None),
    ("ADVERSARIAL", "как прошёл день", "none", None),
    ("ADVERSARIAL", "пожал 80 кг утром", "training", None),
    ("ADVERSARIAL", "сейчас поем омлет", "none", "general"),
    ("ADVERSARIAL", "буду есть омлет", "none", "general"),
    # CONTROL — must keep working
    ("CONTROL", "пробежал 5 км", "training", None),
    ("CONTROL", "прошёл 6 км", "training", None),
    ("CONTROL", "съел омлет, люблю его", "meal", "meal"),
    ("CONTROL", "сегодня 82 кг утром", "weight", None),
    # NOTE — physical observations are remembered (Vlad: боль/ограничения)
    ("NOTE", "болит плечо", "note", None),
    ("NOTE", "болит плечо после жима", "note", None),
    ("NOTE", "потянул спину на становой", "note", None),
]

INTENT_CASES = [
    ("сорвался вечером, сожрал пол-холодильника", "behaviorist"),
    ("думаю съесть побольше белка, стоит ли?", "general"),
    ("утром 3 яйца, тост и авокадо", "meal"),
    ("присед 100 кг 5х5, как прогрессия?", "training"),
    ("спал 5 часов, разбитый", "sleep_recovery"),
    ("сдал анализы: ApoB 80, LDL 3.1", "biomarkers_imaging"),
    ("стоит ли сейчас уходить в дефицит или держать поддержку?", "general"),
]

P4_CASES = [
    "стоит ли уходить в дефицит или держать поддержку?",
    "как лучше восстановиться после недосыпа?",
]


def expectations():
    out = []
    for sec, msg, fact, role in EFFECTIVE_CASES:
        out.append({
            "section": sec, "msg": msg,
            "loggable": fact != "none", "log_type": fact,
            "intent": role if sec in ("C role<->write", "MIXED") else None,
            "safety": sec in SAFETY_SECTIONS,
        })
    for msg, role in INTENT_CASES:
        out.append({"section": "intent-7", "msg": msg, "loggable": None,
                    "log_type": None, "intent": role, "safety": False})
    for msg in P4_CASES:
        out.append({"section": "P4", "msg": msg, "loggable": False,
                    "log_type": "none", "intent": None, "safety": False})
    return out


def passes(out, exp):
    if out is None:
        return False
    if exp["loggable"] is not None and bool(out.get("loggable")) != exp["loggable"]:
        return False
    if exp["loggable"] is True and out.get("log_type") != exp["log_type"]:
        return False
    if exp["loggable"] is False and out.get("log_type") not in (None, "none"):
        return False
    if exp["intent"] is not None and out.get("intent") != exp["intent"]:
        return False
    return True


def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY missing — eval needs real LLM calls.")
        return 2

    cases = expectations()
    jobs = [(i, r) for i in range(len(cases)) for r in range(N)]

    def run(job):
        i, _r = job
        # shadow_classify swallows transport errors as None; retry with backoff
        # so transient API hiccups don't read as quality fails.
        for attempt in range(5):
            out = bot.shadow_classify(cases[i]["msg"])
            if out is not None:
                return i, out
            time.sleep(2 ** (attempt + 1))
        return i, None

    raw = {i: [] for i in range(len(cases))}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, out in pool.map(run, jobs):
            raw[i].append(out)

    rows = []
    transport_errors = 0
    for i, exp in enumerate(cases):
        outs = [o for o in raw[i] if o is not None]
        transport_errors += sum(1 for o in raw[i] if o is None)
        oks = [passes(o, exp) for o in outs]
        rows.append({
            "exp": exp, "ok": sum(oks), "valid": len(outs),
            "bad": next((o for o, k in zip(outs, oks) if not k), None),
        })

    width = min(50, max(len(r["exp"]["msg"]) for r in rows))
    print(f"{'SECTION':<14} | {'MESSAGE':<{width}} | OK/valid")
    print("-" * (14 + width + 12))
    for r in rows:
        m = r["exp"]["msg"]
        m = m if len(m) <= width else m[: width - 1] + "…"
        if r["valid"] == 0:
            mark = "TRANSPORT"
        elif r["ok"] == r["valid"]:
            mark = "PASS"
        else:
            mark = "FLAKY" if r["ok"] else "FAIL"
        print(f"{r['exp']['section']:<14} | {m:<{width}} | {r['ok']}/{r['valid']} {mark}")

    print("\n=== QUALITY FAILURES (valid responses only) ===")
    fails = [r for r in rows if r["valid"] and r["ok"] < r["valid"]]
    for r in fails:
        e = r["exp"]
        tag = "SAFETY-FAIL" if e["safety"] else "FAIL"
        print(f"[{tag}] {e['section']} | {e['msg']}  ({r['ok']}/{r['valid']})")
        print(f"    expected loggable={e['loggable']} log_type={e['log_type']} "
              f"intent={e['intent']}  sample: {r['bad']}")
    if not fails:
        print("(none)")

    def rate(safety):
        sel = [r for r in rows if r["exp"]["safety"] == safety]
        ok = sum(r["ok"] for r in sel)
        total = sum(r["valid"] for r in sel)
        return ok, total, (ok / total if total else 1.0)

    s_ok, s_tot, s = rate(True)
    o_ok, o_tot, o = rate(False)
    total_runs = len(rows) * N
    transport_rate = transport_errors / total_runs
    print("\n=== SUMMARY (LLM-alone = prod behavior; quality over valid runs) ===")
    print(f"transport errors: {transport_errors}/{total_runs} runs ({transport_rate:.1%})")
    print(f"safety:     {s_ok}/{s_tot} ({s:.3f})  target 1.000")
    print(f"non-safety: {o_ok}/{o_tot} ({o:.3f})  target >= 0.950")
    if transport_rate > 0.10:
        print("\nGATE: INCONCLUSIVE — transport error rate too high to certify; re-run when API is stable.")
        return 3
    gate = s == 1.0 and o >= 0.95
    print(f"\nGATE: {'PASS' if gate else 'FAIL'}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
