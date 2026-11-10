import os
import json
import time
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_MODEL = "gemini-3.8-flash"   # set to "" to skip Gemini and save its daily quota
CACHE_FILE = "judge_cache.json"


def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def build_prompt(brief, work):
    return f"""Compare the WORK with the BRIEF.
BRIEF: {brief}
WORK: {work}

List the requirements from the brief (max 4). Each note: 6 words or fewer.
"decision" is "release" only if all important requirements are met, else "cancel".
"summary" is one short sentence.
Reply ONLY with JSON:
{{"checklist":[{{"requirement":"...","met":true,"note":"..."}}],"decision":"release","summary":"..."}}"""


def ask_gemini(prompt):
    def call(config):
        r = gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
        return json.loads(r.text)

    base = dict(
        response_mime_type="application/json",
        temperature=0,
        http_options=types.HttpOptions(timeout=10000),
    )
    try:
        # thinking off = much faster
        return call(types.GenerateContentConfig(
            **base, thinking_config=types.ThinkingConfig(thinking_budget=0)))
    except Exception as e:
        if "400" in str(e) or "thinking" in str(e).lower():
            return call(types.GenerateContentConfig(**base))
        raise


def ask_compat(prefix, prompt, model=None):
    # OpenRouter (BACKUP) and any similar provider (FAST) use the same request format
    r = requests.post(
        os.getenv(f"{prefix}_BASE_URL") + "/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv(prefix + '_API_KEY')}"},
        json={
            "model": model or os.getenv(f"{prefix}_MODEL"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 400,
        },
        timeout=12,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"].get("content")
    if not text:
        raise ValueError("empty reply")
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("no JSON in reply")
    return json.loads(text[s:e + 1])


def get_racers(prompt):
    """Everything that is set up in .env becomes a racer."""
    racers = []
    if GEMINI_MODEL and os.getenv("GEMINI_API_KEY"):
        racers.append(("Gemini", lambda: ask_gemini(prompt)))
    if os.getenv("FAST_API_KEY") and os.getenv("FAST_BASE_URL") and os.getenv("FAST_MODEL"):
        racers.append(("Fast AI", lambda: ask_compat("FAST", prompt)))
    if os.getenv("BACKUP_API_KEY") and os.getenv("BACKUP_BASE_URL"):
        for m in (os.getenv("BACKUP_MODEL") or "").split(","):
            m = m.strip()
            if m:
                racers.append((f"OpenRouter {m.split('/')[-1][:22]}",
                               lambda m=m: ask_compat("BACKUP", prompt, m)))
    return racers


def valid(res):
    return (
        isinstance(res, dict)
        and res.get("decision") in ("release", "cancel")
        and isinstance(res.get("checklist"), list)
        and len(res["checklist"]) > 0
    )


def judge_work(brief, delivered_work):
    # Same brief + same work = instant answer from the cache
    key = hashlib.sha256((brief + "|" + delivered_work).encode()).hexdigest()
    cache = load_cache()
    if key in cache:
        print("Answered from cache (instant)")
        return cache[key]

    prompt = build_prompt(brief, delivered_work)
    racers = get_racers(prompt)
    result = None
    start = time.time()

    if racers:
        ex = ThreadPoolExecutor(max_workers=len(racers))
        futures = {ex.submit(fn): name for name, fn in racers}
        try:
            for f in as_completed(futures, timeout=15):
                name = futures[f]
                try:
                    res = f.result()
                    if valid(res):
                        result = res
                        print(f"{name} won in {time.time() - start:.1f}s")
                        break
                    print(f"{name} gave an unusable answer")
                except Exception as e:
                    print(f"{name} failed:", str(e)[:80])
        except Exception:
            pass
        ex.shutdown(wait=False, cancel_futures=True)

    if result is None:
        raise RuntimeError(
            "The AI judge is busy right now. Your money is still safely held. "
            "Please try again in a minute."
        )

    cache[key] = result
    save_cache(cache)
    return result


if __name__ == "__main__":
    brief = "Write a 3-line slogan for a tea stall. Must mention 'chai' and be under 15 words per line."
    work = "Fresh tea, fresh start.\nWarm cups, warm hearts.\nCome sip happiness today."

    begin = time.time()
    result = judge_work(brief, work)
    for item in result["checklist"]:
        mark = "YES" if item["met"] else "NO "
        print(f"[{mark}] {item['requirement']} - {item['note']}")
    print("\nDecision:", result["decision"])
    print("Summary:", result["summary"])
    print(f"Total: {time.time() - begin:.1f}s")