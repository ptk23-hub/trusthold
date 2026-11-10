import sys
import time
from ai_judge import get_racers, build_prompt, judge_work, valid

BRIEF = "Write a 3-line slogan for a tea stall. Must mention 'chai' and be under 15 words per line."
WORK = "Fresh tea, fresh start.\nWarm cups, warm hearts.\nCome sip happiness today."

runs = int(sys.argv[1]) if len(sys.argv) > 1 else 1
racers = get_racers(build_prompt(BRIEF, WORK))

print(f"=== Each racer alone ({len(racers)} found) ===")
for name, fn in racers:
    for _ in range(runs):
        start = time.time()
        try:
            res = fn()
            tag = "OK  " if valid(res) else "BAD "
            print(f"{name:34} {tag} {time.time() - start:.1f}s  decision={res.get('decision')}")
        except Exception as e:
            print(f"{name:34} FAIL {time.time() - start:.1f}s  {str(e)[:60]}")
        time.sleep(1)

print("\n=== Full race ===")
start = time.time()
try:
    # a timestamp makes the text new, so the cache can't answer for it
    res = judge_work(BRIEF, WORK + f" [{time.time()}]")
    print(f"Race finished in {time.time() - start:.1f}s  decision={res['decision']}")
except Exception as e:
    print("Race failed:", str(e)[:100])