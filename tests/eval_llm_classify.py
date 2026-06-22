"""Eval gate for LLM-primary classification (path b).

Runs the 34 harness cases (from test_classify.py) through the REAL LLM
classifier `bot.shadow_classify()`, N times each (temp 0; N runs measure
flakiness), and scores TWO ways:

  (a) LLM-alone  — how well the model understands by itself. Higher = less we
      lean on regex = more faithful to Vlad (understanding, not pattern-match).
  (b) LLM+guard  — production-faithful: the thin deterministic safety guard from
      design 3.5 (is_setback_message / is_intention_or_opinion / question /
      planning) applied on top. The guard may only NARROW (force not-loggable,
      or behaviorist for a setback), never widen. This is the SWITCH number.

Expectation mapping (LLM shape {intent, loggable, log_type}):
- don't-write (fact "none"): loggable=false, log_type=none.
- write (meal/weight/sleep/training): loggable=true + that log_type.
- intent checked only where meaningful: C (behaviorist), MIXED (meal), intent-7.
- P4 (questions / pain note): not a trackable fact -> loggable=false.

SAFETY set (gate 100% on LLM+guard): A ("no-write") + C (no-write & behaviorist).
Non-safety gate: >= 0.95 on LLM+guard.

Needs ANTHROPIC_API_KEY. Cost: 34 x N Haiku calls. Does not modify bot.py.
Run: python3 tests/eval_llm_classify.py
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HEALTH_OS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HEALTH_OS))
sys.path.insert(0, str(HEALTH_OS / "tests"))

import bot  # noqa: E402
from test_classify import EFFECTIVE_CASES, INTENT_CASES, P4_CASES  # noqa: E402

N = 5
WORKERS = 6
SAFETY_SECTIONS = {"A no-write", "C role<->write"}


def expectations():
    out = []
    for sec, msg, fact, role in EFFECTIVE_CASES:
        out.append({
            "section": sec,
            "msg": msg,
            "loggable": fact != "none",
            "log_type": fact,
            "intent": role if sec in ("C role<->write", "MIXED") else None,
            "safety": sec in SAFETY_SECTIONS,
        })
    for msg, role in INTENT_CASES:
        out.append({"section": "intent-7", "msg": msg, "loggable": None,
                    "log_type": None, "intent": role, "safety": False})
    for msg, _notes in P4_CASES:
        out.append({"section": "P4", "msg": msg, "loggable": False,
                    "log_type": "none", "intent": None, "safety": False})
    return out


def apply_guard(text, out):
    """Production safety guard (design 3.5): deterministic, only narrows.
    Mirrors what the switch will do on top of the LLM. Reuses bot predicates."""
    if out is None:
        return None
    g = dict(out)
    if bot.is_setback_message(text):
        g["intent"] = "behaviorist"
        g["loggable"] = False
        g["log_type"] = "none"
    elif (
        bot.is_intention_or_opinion(text)
        or bot.is_question_message(text)
        or bot.is_planning_or_advice_query(text)
        or bot.is_decision_or_planning_question(text)
    ):
        g["loggable"] = False
        g["log_type"] = "none"
    return g


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


def rate(rows, key, safety):
    sel = [r for r in rows if r["exp"]["safety"] == safety]
    ok = sum(r[key] for r in sel)
    total = len(sel) * N
    return ok, total, (ok / total if total else 1.0)


def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY missing — eval needs real LLM calls.")
        return 2

    cases = expectations()
    jobs = [(i, r) for i in range(len(cases)) for r in range(N)]

    def run(job):
        i, _r = job
        return i, bot.shadow_classify(cases[i]["msg"])

    raw = {i: [] for i in range(len(cases))}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, out in pool.map(run, jobs):
            raw[i].append(out)

    rows = []
    for i, exp in enumerate(cases):
        outs = raw[i]
        alone = [passes(o, exp) for o in outs]
        guard = [passes(apply_guard(exp["msg"], o), exp) for o in outs]
        rows.append({
            "exp": exp,
            "alone_ok": sum(alone),
            "guard_ok": sum(guard),
            "alone_bad": next((o for o, ok in zip(outs, alone) if not ok), None),
            "guard_bad": next(
                (apply_guard(exp["msg"], o) for o, ok in zip(outs, guard) if not ok),
                None,
            ),
        })

    width = min(50, max(len(r["exp"]["msg"]) for r in rows))
    print(f"{'SECTION':<14} | {'MESSAGE':<{width}} | alone | +guard")
    print("-" * (14 + width + 18))
    for r in rows:
        m = r["exp"]["msg"]
        m = m if len(m) <= width else m[: width - 1] + "…"
        print(f"{r['exp']['section']:<14} | {m:<{width}} | "
              f"{r['alone_ok']}/{N}   | {r['guard_ok']}/{N}")

    print("\n=== GATE-RELEVANT FAILURES (LLM+guard) ===")
    gate_fail = False
    for r in rows:
        if r["guard_ok"] < N:
            gate_fail = True
            e = r["exp"]
            tag = "SAFETY-FAIL" if e["safety"] else "FAIL"
            print(f"[{tag}] {e['section']} | {e['msg']}")
            print(f"    expected loggable={e['loggable']} log_type={e['log_type']} "
                  f"intent={e['intent']}  ({r['guard_ok']}/{N})")
            print(f"    sample (post-guard): {r['guard_bad']}")
    if not gate_fail:
        print("(none)")

    print("\n=== LLM-ALONE GAPS (model understanding, informational) ===")
    any_gap = False
    for r in rows:
        if r["alone_ok"] < N:
            any_gap = True
            e = r["exp"]
            print(f"[{e['section']}] {e['msg']}  ({r['alone_ok']}/{N})  "
                  f"sample: {r['alone_bad']}")
    if not any_gap:
        print("(none — model passes standalone)")

    a_s_ok, a_s_tot, a_s = rate(rows, "alone_ok", True)
    a_o_ok, a_o_tot, a_o = rate(rows, "alone_ok", False)
    g_s_ok, g_s_tot, g_s = rate(rows, "guard_ok", True)
    g_o_ok, g_o_tot, g_o = rate(rows, "guard_ok", False)

    print("\n=== SUMMARY ===")
    print(f"{'':22} {'safety':>16} {'non-safety':>16}")
    print(f"{'LLM-alone':22} {f'{a_s_ok}/{a_s_tot} ({a_s:.3f})':>16} "
          f"{f'{a_o_ok}/{a_o_tot} ({a_o:.3f})':>16}")
    print(f"{'LLM+guard (switch)':22} {f'{g_s_ok}/{g_s_tot} ({g_s:.3f})':>16} "
          f"{f'{g_o_ok}/{g_o_tot} ({g_o:.3f})':>16}")

    gate_safety = g_s == 1.0
    gate_other = g_o >= 0.95
    print(f"\nSWITCH GATE (LLM+guard): safety {'PASS' if gate_safety else 'FAIL'} "
          f"(target 1.000) | non-safety {'PASS' if gate_other else 'FAIL'} (target >= 0.950)")
    print(f"LLM-alone (Vlad fidelity, informational): "
          f"safety {a_s:.3f}, non-safety {a_o:.3f}")
    return 0 if (gate_safety and gate_other) else 1


if __name__ == "__main__":
    sys.exit(main())
