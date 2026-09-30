"""Run the extraction eval on data/gold_30.jsonl and save predictions + run metadata.

Usage (key via the environment only):  python eval/run_eval.py
Writes eval/predictions_t0.jsonl and eval/run_meta_t0.json, then run eval/report.py.
"""

import datetime
import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

# Make the repo root importable so the shared prompt / extractor are used (python eval/run_eval.py)
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(EVAL_DIR, ".."))
from extractor import extract_crm_data  # noqa: E402
from prompts import API_BASE_URL, MODEL_NAME, TEMPERATURE  # noqa: E402

DATA_PATH = os.path.join(EVAL_DIR, "..", "data", "gold_30.jsonl")
PRED_PATH = os.path.join(EVAL_DIR, "predictions_t0.jsonl")
META_PATH = os.path.join(EVAL_DIR, "run_meta_t0.json")


def load_gold(path=DATA_PATH):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run_eval():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("AICREDITS_API_KEY"), base_url=API_BASE_URL)
    records = load_gold()
    print(f"Starting evaluation of {len(records)} notes using {MODEL_NAME} (temperature={TEMPERATURE})...")

    rows = []
    for idx, record in enumerate(records, start=1):
        print(f"Processing note {idx}/{len(records)}...")
        result = extract_crm_data(client, record["input"])
        if not result["success"]:
            print(f"  extraction error: {result['error']}")
        rows.append({
            "note_id": idx,
            "input": record["input"],
            "expected": record["expected"],
            "predicted": result.get("data", {}) if result["success"] else {},
            "success": result["success"],
            "error": result.get("error"),
            "latency_s": result.get("latency"),
            "prompt_tokens": result.get("prompt_tokens"),
            "completion_tokens": result.get("completion_tokens"),
            "total_tokens": result.get("total_tokens"),
        })
        time.sleep(1)

    with open(PRED_PATH, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    latencies = [r["latency_s"] for r in rows if r["latency_s"] is not None]
    meta = {
        "run_date_ist": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).isoformat(timespec="minutes"),
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "notes": len(rows),
        "api_calls": len(rows),
        "failed_calls": sum(1 for r in rows if not r["success"]),
        "prompt_tokens": sum(r["prompt_tokens"] or 0 for r in rows),
        "completion_tokens": sum(r["completion_tokens"] or 0 for r in rows),
        "total_tokens": sum(r["total_tokens"] or 0 for r in rows),
        "avg_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else None,
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {PRED_PATH} and {META_PATH}. Next: python eval/judge.py && python eval/report.py")


if __name__ == "__main__":
    run_eval()
