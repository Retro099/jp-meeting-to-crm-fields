"""Build eval/results.md from eval/predictions_t0.jsonl, eval/judge_results.jsonl and the run metadata.

No API calls.  Usage:  python eval/report.py [--usd-inr 96.06]
"""

import argparse
import json
import os
import sys

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EVAL_DIR)
from scoring import FIELDS, JUDGED_FIELDS, overall, score_exact, summarize_verdicts  # noqa: E402

# AICredits bills the upstream (OpenRouter) rate, converted to INR with a 5% forex buffer + 5% platform fee.
USD_PER_M_INPUT = 0.36
USD_PER_M_OUTPUT = 0.40
FEES = 1.05 * 1.05


def load_jsonl(name):
    with open(os.path.join(EVAL_DIR, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json(name):
    with open(os.path.join(EVAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def inr_estimate(prompt_tokens, completion_tokens, usd_inr):
    usd = prompt_tokens / 1e6 * USD_PER_M_INPUT + completion_tokens / 1e6 * USD_PER_M_OUTPUT
    return usd * FEES * usd_inr


def pct(x):
    return f"{100 * x:.1f}%"


def build(usd_inr):
    preds = load_jsonl("predictions_t0.jsonl")
    judged = load_jsonl("judge_results.jsonl")
    meta = load_json("run_meta_t0.json")
    jmeta = load_json("judge_meta.json")

    scores = score_exact((r["expected"], r["predicted"]) for r in preds)
    correct, total = overall(scores)
    sem = {f: summarize_verdicts([j["verdict"] for j in judged if j["field"] == f and j["verdict"]])
           for f in JUDGED_FIELDS}

    out = ["# 評価結果 (Evaluation Results)", "",
           f"Measured at temperature=0 on {meta['run_date_ist'][:10]} with `{meta['model']}` "
           f"on the 30 labelled notes in `data/gold_30.jsonl`.", "",
           "## フィールド別精度 (Field Accuracy)", "",
           "| フィールド (Field) | Exact match | 正解数 (Correct/Total) | LLM-judge (semantic) | LLM-judge strict (match only) |",
           "| --- | --- | --- | --- | --- |"]
    for f in FIELDS:
        s = scores[f]
        if f in sem:
            c = sem[f]["counts"]
            sem_cell = f"{pct(sem[f]['semantic_score'])} ({c['match']} match / {c['partial']} partial / {c['miss']} miss)"
            strict_cell = f"{pct(sem[f]['strict_match_rate'])} ({c['match']}/{sem[f]['n']})"
        else:
            sem_cell = strict_cell = "—"
        out.append(f"| {f} | {pct(s['correct'] / s['total'])} | {s['correct']}/{s['total']} | {sem_cell} | {strict_cell} |")
    out.append(f"| **Overall** | **{pct(correct / total)}** | **{correct}/{total}** | — | — |")
    out += ["",
            "- **Exact match**: the predicted string must equal the gold string after trimming whitespace.",
            "- **LLM-judge (semantic)**: only for 次アクション and リスク. The same model grades each prediction "
            "against the gold answer (`eval/judge.py`, prompt in `eval/judge_prompt.txt`, temperature 0): "
            "match = 1, partial = 0.5, miss = 0. The strict column counts `match` only.",
            "- **Limitation**: the judge is the same model family as the extractor, so it may be biased in favour "
            "of its own wording (self-judging bias). Treat the semantic column as a rough guide, not ground truth.",
            "", "## History (overall exact match)", "",
            "| Iteration | Overall |", "| --- | --- |",
            "| Iteration 1 | 28.7% |",
            "| Iteration 2 | 53.3% |",
            "| Iteration 3 — before temperature=0 ([details](results_pre_t0.md)) | 56.0% |",
            f"| Iteration 4 — same prompt, temperature=0 (this run) | {pct(correct / total)} |",
            "", "## Cost and latency (measured)", ""]
    ext_inr = inr_estimate(meta["prompt_tokens"], meta["completion_tokens"], usd_inr)
    j_inr = inr_estimate(jmeta["prompt_tokens"], jmeta["completion_tokens"], usd_inr)
    out += ["| Run | API calls | Prompt tokens | Completion tokens | Total tokens | Est. cost | Avg latency |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            f"| Extraction (30 notes) | {meta['api_calls']} | {meta['prompt_tokens']:,} | {meta['completion_tokens']:,} | "
            f"{meta['total_tokens']:,} | ≈ ₹{ext_inr:.2f} | {meta['avg_latency_s']} s / note |",
            f"| LLM judge | {jmeta['api_calls']} | {jmeta['prompt_tokens']:,} | {jmeta['completion_tokens']:,} | "
            f"{jmeta['total_tokens']:,} | ≈ ₹{j_inr:.2f} | {jmeta['avg_latency_s']} s / call |",
            "",
            f"Cost is an estimate: ${USD_PER_M_INPUT}/M input and ${USD_PER_M_OUTPUT}/M output tokens (upstream rate), "
            f"× 1.05 forex buffer × 1.05 platform fee (AICredits pricing docs), at USD/INR {usd_inr} (open.er-api.com rate, 2026-09-30). "
            "The AICredits dashboard shows the exact amount charged.", ""]
    if meta.get("failed_calls") or jmeta.get("failed_calls"):
        out += [f"Failed calls: extraction {meta.get('failed_calls', 0)}, judge {jmeta.get('failed_calls', 0)} "
                "(a failed extraction counts as empty, i.e. wrong).", ""]

    if os.path.exists(os.path.join(EVAL_DIR, "judge_spotcheck.md")):
        out += ["A manual spot-check of the judge verdicts is in [judge_spotcheck.md](judge_spotcheck.md).", ""]
    out += ["## 抽出エラー (Failure Logs, exact match)", ""]
    jmap = {(j["note_id"], j["field"]): j for j in judged}
    for r in preds:
        diffs = [f for f in FIELDS if str(r["expected"].get(f, "")).strip() != str(r["predicted"].get(f, "")).strip()]
        if not diffs:
            continue
        out += [f"### Note {r['note_id']}", f"**Input:** {r['input']}", ""]
        if r.get("error"):
            out.append(f"- extraction error: `{r['error']}`")
        for f in diffs:
            out += [f"- **{f}**", f"  - Expected: `{r['expected'].get(f, '')}`",
                    f"  - Extracted: `{r['predicted'].get(f, '')}`"]
            j = jmap.get((r["note_id"], f))
            if j and j.get("verdict"):
                out.append(f"  - LLM judge: {j['verdict']} — {j['reason']}")
        out.append("")
    with open(os.path.join(EVAL_DIR, "results.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"Overall exact match {correct}/{total} = {pct(correct / total)}")
    print(json.dumps(sem, ensure_ascii=False))
    print(f"Est. cost: extraction ₹{ext_inr:.3f}, judge ₹{j_inr:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--usd-inr", type=float, default=96.06)
    build(ap.parse_args().usd_inr)
