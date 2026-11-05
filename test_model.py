import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("BACKUP_API_KEY")
base = os.getenv("BACKUP_BASE_URL")

if len(sys.argv) < 2:
    # No model given: list the models your key can see
    r = requests.get(base + "/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    print("Status:", r.status_code)
    for m in sorted(x["id"] for x in r.json()["data"]):
        print(m)
else:
    # Test one model with a tiny request
    r = requests.post(
        base + "/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": sys.argv[1],
              "messages": [{"role": "user", "content": "Reply with just the word OK"}],
              "max_tokens": 20},
        timeout=60,
    )
    print("Status:", r.status_code)
    print(r.text[:300])