"""Full-day simulation against a REAL temp log file.

Drives handle_message + /today end to end with real file I/O, then asserts what
actually landed on disk. This is the net that caught the /today crash, the
private-flag leak into the YAML, and meal-correction duplicates.

Needs ANTHROPIC_API_KEY (makes real calls). Run: python3 tests/test_full_day.py
"""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bot
import yaml

# Redirect log writes to a temp dir (real file I/O, real YAML).
TMP = Path(tempfile.mkdtemp(prefix="healthos_test_"))
bot.LOGS_DIR = TMP


class M:
    def __init__(s, t): s.text = t; s.caption = None; s.replies = []
    async def reply_text(s, t): s.replies.append(t)


class U:
    username = "roman"; id = 461299547


class Upd:
    def __init__(s, t): s.message = M(t); s.effective_user = U()


def send(text):
    u = Upd(text)
    asyncio.run(asyncio.wait_for(bot.handle_message(u, None), timeout=120))
    return u.message.replies[-1] if u.message.replies else "(нет ответа)"


DAY = [
    ("утро, вес 82.4", "вес"),
    ("спал 7 часов, проснулся бодрым", "сон"),
    ("на завтрак съел творог простоквашино 5% 120 г и банан", "еда"),
    ("в твороге было 121 ккал и 18 г белка", "уточнение еды"),
    ("Лег пресс 80 кг 3 подхода 10 повторений, жим на наклонной 60 кг 3 по 10, "
     "на плечи в тренажере матрикс 20 кг 3 по 10, трицепс на канате 23 кг 3 по 10, "
     "бицепс 10 кг 3 по 10, махи на переднюю дельту 6 кг 3 по 10", "тренировка"),
    ("? а всё остальное", "уточняющий вопрос"),
    ("болит правое плечо после жима", "боль"),
    ("зачем чередовать сауну и холод?", "вопрос по знаниям"),
    ("вечером сорвался, наелся сладкого", "срыв"),
]

print("=" * 78)
for text, label in DAY:
    reply = send(text)
    first = reply.splitlines()[0][:74]
    print(f"[{label:18}] {text[:44]!r}")
    print(f"{'':21}→ {first}")
print("=" * 78)

# --- inspect what actually hit disk ---
log_file = TMP / f"{bot.today_str()}.yaml"
raw = log_file.read_text(encoding="utf-8")
data = yaml.safe_load(raw)

print("\n=== ЧТО ЗАПИСАНО НА ДИСК ===")
print(f"вес: {data.get('weight_morning')}")
print(f"сон: {data.get('sleep', {}).get('hours')} ч, качество={data.get('sleep', {}).get('quality')}")
print(f"приёмов пищи: {len(data.get('meals') or [])}")
for m in data.get("meals") or []:
    print(f"   - {m.get('description')!r} | {m.get('calories')} ккал, Б {m.get('protein_g')}")
tr = data.get("training") or []
print(f"тренировок: {len(tr)}, упражнений: {len(tr[-1].get('exercises', [])) if tr else 0}")
for e in (tr[-1].get("exercises") if tr else [])[:7]:
    if isinstance(e, dict):
        print(f"   - {e.get('name')}: {e.get('weight_kg') or e.get('weight')} кг {e.get('sets')}x{e.get('reps')}")
print(f"заметок: {len(data.get('notes') or [])}")
for n in data.get("notes") or []:
    print(f"   - {n.get('text')!r}")

print("\n=== /today ===")
u = Upd("/today")
bot.read_daily_log_orig = bot.read_daily_log
asyncio.run(asyncio.wait_for(bot.today(u, None), timeout=60))
print(u.message.replies[-1][:400])

# --- quality gates ---
private = [k for k in data if str(k).startswith("_")]
checks = [
    ("вес записан (82.4)", data.get("weight_morning") == 82.4),
    ("сон записан (7 ч)", (data.get("sleep") or {}).get("hours") == 7),
    ("еда: уточнение НЕ создало дубль (1 приём)", len(data.get("meals") or []) == 1),
    ("еда: калории обновлены на 121", (data.get("meals") or [{}])[0].get("calories") == 121),
    ("тренировка: одна сессия", len(tr) == 1),
    ("тренировка: >=5 упражнений", len(tr[-1].get("exercises", [])) >= 5 if tr else False),
    ("боль записана в notes", len(data.get("notes") or []) >= 1),
    ("срыв НЕ записан как еда (всё ещё 1 приём)", len(data.get("meals") or []) == 1),
    ("нет служебных ключей в YAML", not private),
    ("YAML валиден и читается", isinstance(data, dict)),
]
print("\n=== ПРОВЕРКИ ===")
ok = True
for name, passed in checks:
    ok = ok and passed
    print(f"  {'PASS' if passed else 'FAIL'} | {name}")
if private:
    print(f"  !! служебные ключи: {private}")

print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if ok else 1)
