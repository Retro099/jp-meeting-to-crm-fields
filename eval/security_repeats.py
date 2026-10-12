"""Summarize repeated defenses-on runs (no API calls): exact match, ASR and provenance flags, mean and range.

Reads predictions_on_r*.jsonl and attacks_on_r*.jsonl in eval/runs/2026-10-12/, writes security_repeats.json there.
"""

import glob
import json
import os
import re
import sys

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EVAL_DIR)
from paths import SECURITY_RUN, read_dir  # noqa: E402
from scoring import overall, score_exact  # noqa: E402


def _load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _run_id(path):
    return int(re.search(r"_r(\d+)", path).group(1))


def provenance_counts(rows, data_key):
    """Fields provenance flagged / blocked, out of all delivered fields."""
    fields = flagged = blocked = 0
    for r in rows:
        sec = r.get("security") or {}
        if r.get(data_key):
            fields += len(r[data_key])
        flagged += len(sec.get("provenance_flagged", []))
        blocked += len(sec.get("provenance_blocked", []))
    return {"fields": fields, "flagged": flagged, "blocked": blocked}


def spread(values):
    return {"runs": values, "mean": round(sum(values) / len(values), 2), "min": min(values), "max": max(values)}


def summarize(eval_dir=None):
    eval_dir = eval_dir or read_dir(SECURITY_RUN)
    runs = []
    for p in sorted(glob.glob(os.path.join(eval_dir, "predictions_on_r*.jsonl")), key=_run_id):
        i = _run_id(p)
        preds = _load(p)
        correct, total = overall(score_exact((r["expected"], r["predicted"]) for r in preds))
        run = {"run": i, "exact_correct": correct, "exact_total": total,
               "exact_pct": round(100 * correct / total, 1), "failed_calls": sum(not r["success"] for r in preds),
               "gold_provenance": provenance_counts(preds, "predicted")}
        ap = os.path.join(eval_dir, f"attacks_on_r{i}.jsonl")
        if os.path.exists(ap):
            att = _load(ap)
            ok = sum(bool(r["attack_success"]) for r in att)
            run.update({"asr_success": ok, "asr_total": len(att), "asr_pct": round(100 * ok / len(att), 1),
                        "attack_failed_calls": sum(not r["success"] for r in att),
                        "attack_successes": [r["id"] for r in att if r["attack_success"]],
                        "attack_provenance": provenance_counts(att, "data")})
        runs.append(run)
    out = {"runs": runs}
    if runs:
        out["exact_pct"] = spread([r["exact_pct"] for r in runs])
        if all("asr_pct" in r for r in runs):
            out["asr_pct"] = spread([r["asr_pct"] for r in runs])
    return out


if __name__ == "__main__":
    s = summarize()
    with open(os.path.join(read_dir(SECURITY_RUN), "security_repeats.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in s.items() if k != "runs"}, ensure_ascii=False))
