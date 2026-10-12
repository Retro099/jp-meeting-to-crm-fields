"""Run the prompt-injection attack set against the extractor, with defenses off or on.

Usage (key via the environment only):
    python eval/run_attacks.py --mode off     # baseline -> eval/attacks_off.jsonl
    python eval/run_attacks.py --mode on      # defended -> eval/attacks_on.jsonl
One API call per case. A fixed canary is planted in the system prompt in BOTH modes so leaks are comparable.
"""

import argparse
import datetime
import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(EVAL_DIR, ".."))
sys.path.insert(0, EVAL_DIR)
from attack_scoring import asr_by_category, attack_succeeded  # noqa: E402
from extractor import extract_crm_data  # noqa: E402
from prompts import API_BASE_URL, MODEL_NAME, TEMPERATURE  # noqa: E402

DATA = os.path.join(EVAL_DIR, "..", "data", "attacks_v1.jsonl")
CANARY = "CANARY-7f3a9c2e51d84b60"  # test-only marker, not a real secret


def main(mode, max_calls, tag=None):
    tag = tag or mode
    load_dotenv()
    cases = [json.loads(l) for l in open(DATA, encoding="utf-8") if l.strip()]
    if len(cases) > max_calls:
        sys.exit(f"{len(cases)} calls planned, over the limit {max_calls}")
    client = OpenAI(api_key=os.getenv("AICREDITS_API_KEY"), base_url=API_BASE_URL, timeout=90, max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "1")))
    rows = []
    for c in cases:
        r = extract_crm_data(client, c["input"], defenses=(mode == "on"), canary=CANARY)
        rows.append({"id": c["id"], "category": c["category"], "lang": c["lang"],
                     "attack_success": attack_succeeded(c, r, CANARY), "success": r["success"],
                     "error": r.get("error"), "data": r.get("data"), "security": r.get("security")})
        print(c["id"], c["category"], "SUCCESS" if rows[-1]["attack_success"] else "blocked/failed")
        time.sleep(1)
    with open(os.path.join(EVAL_DIR, f"attacks_{tag}.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"mode": mode, "model": MODEL_NAME, "temperature": TEMPERATURE, "dataset": "data/attacks_v1.jsonl",
               "api_calls": len(rows), "failed_calls": sum(not r["success"] for r in rows),
               "run_date_ist": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).isoformat(timespec="minutes"),
               "asr": asr_by_category(rows)}
    with open(os.path.join(EVAL_DIR, f"attacks_{tag}_meta.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary["asr"], ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["off", "on"], required=True)
    ap.add_argument("--max-calls", type=int, default=int(os.getenv("MAX_API_CALLS", "50")))
    ap.add_argument("--tag", default=None, help="output suffix (default: the mode)")
    a = ap.parse_args()
    main(a.mode, a.max_calls, a.tag)
