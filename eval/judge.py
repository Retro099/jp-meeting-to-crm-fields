"""LLM-as-judge (semantic) scoring for 次アクション and リスク on eval/predictions_t0.jsonl.

Same model as the extractor, temperature 0, JSON output {verdict: match|partial|miss, reason}.
Scores: match=1, partial=0.5, miss=0; the strict count uses match only.
Limitation: the judge is the same model family as the extractor (self-judging bias).

Usage (key via the environment only):  python eval/judge.py
Writes eval/judge_results.jsonl and eval/judge_meta.json.
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(EVAL_DIR, ".."))
sys.path.insert(0, EVAL_DIR)
from prompts import API_BASE_URL, MODEL_NAME  # noqa: E402
from scoring import JUDGED_FIELDS, exact_match, parse_verdict, summarize_verdicts  # noqa: E402

JUDGE_TEMPERATURE = 0
PROMPT_PATH = os.path.join(EVAL_DIR, "judge_prompt.txt")
PRED_PATH = os.path.join(EVAL_DIR, "predictions_t0.jsonl")
OUT_PATH = os.path.join(EVAL_DIR, "judge_results.jsonl")
META_PATH = os.path.join(EVAL_DIR, "judge_meta.json")


def load_prompt(path=PROMPT_PATH):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build_judge_prompt(template, field, note, gold, pred):
    return (template.replace("<<FIELD>>", field)
            .replace("<<NOTE>>", note)
            .replace("<<GOLD>>", str(gold))
            .replace("<<PRED>>", str(pred) if str(pred).strip() else "(空 / empty)"))


def judge_one(client, template, field, note, gold, pred):
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": build_judge_prompt(template, field, note, gold, pred)}],
        response_format={"type": "json_object"},
        temperature=JUDGE_TEMPERATURE,
    )
    latency = round(time.perf_counter() - start, 2)
    usage = response.usage
    parsed = parse_verdict(response.choices[0].message.content)
    tokens = (getattr(usage, "prompt_tokens", 0) or 0, getattr(usage, "completion_tokens", 0) or 0)
    return parsed, latency, tokens


def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("AICREDITS_API_KEY"), base_url=API_BASE_URL)
    template = load_prompt()
    with open(PRED_PATH, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    results, prompt_tokens, completion_tokens, latencies, errors = [], 0, 0, [], 0
    for row in rows:
        for field in JUDGED_FIELDS:
            gold = row["expected"].get(field, "")
            pred = row["predicted"].get(field, "")
            try:
                parsed, latency, tokens = judge_one(client, template, field, row["input"], gold, pred)
            except Exception as e:  # keep going; record the failure honestly
                errors += 1
                parsed, latency, tokens = {"verdict": None, "reason": f"judge error: {e}"}, None, (0, 0)
            prompt_tokens += tokens[0]
            completion_tokens += tokens[1]
            if latency is not None:
                latencies.append(latency)
            results.append({"note_id": row["note_id"], "field": field, "gold": gold, "predicted": pred,
                            "exact_match": exact_match(gold, pred), **parsed})
            print(f"note {row['note_id']:>2} {field}: {parsed['verdict']}")
            time.sleep(0.5)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {f: summarize_verdicts([r["verdict"] for r in results if r["field"] == f and r["verdict"]])
               for f in JUDGED_FIELDS}
    meta = {"model": MODEL_NAME, "temperature": JUDGE_TEMPERATURE, "api_calls": len(results),
            "failed_calls": errors, "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens,
            "avg_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "summary": summary}
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
