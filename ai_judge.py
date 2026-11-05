import os
import json
import time
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Main AI. Add other flash model names that worked for you from list_models.py
GEMINI_MODELS = ["gemini-3.8-flash"]


def build_prompt(brief, delivered_work):
    return f"""You are a fair, neutral referee between a client and a freelancer.

CLIENT'S BRIEF (what was promised):
{brief}

FREELANCER'S DELIVERED WORK:
{delivered_work}

Break the brief into separate requirements. For each one, say whether the
delivered work meets it. Then decide: "release" if all the important
requirements are met, otherwise "cancel".

Reply ONLY with JSON in this format:
{{
  "checklist": [{{"requirement": "...", "met": true, "note": "short reason"}}],
  "decision": "release" or "cancel",
  "summary": "one or two sentences for the client"
}}"""


def ask_gemini(model, prompt):
    response = gemini.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)


def ask_backup(prompt):
    # Backup AI. Works with OpenRouter, Cerebras, NVIDIA or any provider with the
    # same request format. Key, address and model come from the .env file.
    r = requests.post(
        os.getenv("BACKUP_BASE_URL") + "/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('BACKUP_API_KEY')}"},
        json={
            "model": os.getenv("BACKUP_MODEL"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000,
        },
        timeout=120,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"].get("content")
    if not text:
        raise ValueError("The backup AI sent an empty reply")
    # Keep only the JSON part, in case the AI adds extra words
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The backup AI did not send JSON")
    return json.loads(text[start:end + 1])


def judge_work(brief, delivered_work):
    prompt = build_prompt(brief, delivered_work)

    # 1) Try Gemini first
    for model in GEMINI_MODELS:
        try:
            return ask_gemini(model, prompt)
        except Exception as e:
            if "503" in str(e):          # busy: wait and try once more
                time.sleep(3)
                try:
                    return ask_gemini(model, prompt)
                except Exception:
                    pass
            # 429 (daily limit) or anything else: move on right away

    # 2) Gemini failed, so use the backup AI
    if os.getenv("BACKUP_API_KEY"):
        try:
            return ask_backup(prompt)
        except Exception as e:
            print("Backup AI error:", str(e)[:300])

    raise RuntimeError(
        "The AI judge is busy right now. Your money is still safely held. "
        "Please try again in a minute."
    )


if __name__ == "__main__":
    brief = "Write a 3-line slogan for a tea stall. Must mention 'chai' and be under 15 words per line."
    work = "Fresh tea, fresh start.\nWarm cups, warm hearts.\nCome sip happiness today."

    result = judge_work(brief, work)
    for item in result["checklist"]:
        mark = "YES" if item["met"] else "NO "
        print(f"[{mark}] {item['requirement']} - {item['note']}")
    print("\nDecision:", result["decision"])
    print("Summary:", result["summary"])