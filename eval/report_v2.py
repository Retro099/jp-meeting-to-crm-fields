"""Turn the eval-v2 checkpoint into the README results tables + limits, and a human spot-check sheet.

No API calls. Usage:
    python eval/report_v2.py --out /workspace/crm-eval-v2      # writes results_v2.md and spotcheck_v2.md there
"""

import argparse
import json
import os
import random
import statistics as st
import sys

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EVAL_DIR)
from scoring import FIELDS, VERDICT_POINTS  # noqa: E402

PATHS = ("old", "agent")


def load(cp):
    with open(cp, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_key(k):
    run, path, note, field = k.split("|")
    return run, path, note, field


def spread(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "n/a"
    sd = st.pstdev(xs) if len(xs) > 1 else 0.0
    return f"{st.mean(xs):.3f} ± {sd:.3f} ({min(xs):.3f}–{max(xs):.3f}, n={len(xs)})"


def pct(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))
    return xs[i]


def by_run(recs, prefix, path):
    runs = {}
    for r in recs:
        run, p, note, field = parse_key(r["key"])
        if run.startswith(prefix) and p == path:
            runs.setdefault(run.rsplit("-", 1)[-1], []).append(r)
    return runs


def build(recs):
    out = ["## Results v2 (same session, old path vs LangGraph agent)", "",
           "Model qwen/qwen-2.5-72b-instruct, temperature 0, 30 gold notes, 3 runs per path. Mean ± std (min–max) over runs.", ""]
    # exact match
    out += ["### Exact match per field", "", "| Field | Old path | LangGraph agent |", "|---|---|---|"]
    for f in FIELDS + ["overall"]:
        row = [f]
        for path in PATHS:
            vals = []
            for _, rs in sorted(by_run(recs, "extract-", path).items()):
                cells = [(r["result"].get("exact") or {}) for r in rs]
                if f == "overall":
                    v = [bool(c.get(x)) for c in cells for x in FIELDS]
                else:
                    v = [bool(c.get(f)) for c in cells]
                vals.append(sum(v) / len(v) if v else None)
            row.append(spread(vals))
        out.append("| " + " | ".join(row) + " |")
    # judge
    out += ["", "### LLM judge per field (match=1, partial=0.5, miss=0; supported = grounded in the note)", "",
            "| Field | Old score | Agent score | Old supported | Agent supported |", "|---|---|---|---|---|"]
    for f in FIELDS:
        cols = {}
        for path in PATHS:
            sc, su = [], []
            for _, rs in sorted(by_run(recs, "judge-", path).items()):
                ok = [r["result"] for r in rs if parse_key(r["key"])[3] == f and r["result"].get("success")]
                sc.append(st.mean(VERDICT_POINTS[o["verdict"]] for o in ok) if ok else None)
                su.append(st.mean(1.0 if o["supported"] else 0.0 for o in ok) if ok else None)
            cols[path] = (spread(sc), spread(su))
        out.append(f"| {f} | {cols['old'][0]} | {cols['agent'][0]} | {cols['old'][1]} | {cols['agent'][1]} |")
    # determinism
    out += ["", "### Run-to-run variation at temperature 0", ""]
    for path in PATHS:
        preds = {}
        for r in recs:
            run, p, note, _ = parse_key(r["key"])
            if run.startswith("extract-") and p == path and r["result"].get("success"):
                preds.setdefault(note, set()).add(json.dumps(r["result"]["predicted"], ensure_ascii=False, sort_keys=True))
        varied = sum(1 for v in preds.values() if len(v) > 1)
        out.append(f"- {path}: {varied}/{len(preds)} notes gave different outputs across runs.")
    # cost / latency / repairs
    out += ["", "### Cost, latency, repairs (extraction phase)", "",
            "| Path | Calls/note | Tokens in/out per note | ₹ per note | p50 latency s | p95 latency s | Repairs (0/1/2) | Still invalid |",
            "|---|---|---|---|---|---|---|---|"]
    for path in PATHS:
        rs = [r for r in recs if r["key"].startswith("extract-") and parse_key(r["key"])[1] == path]
        if not rs:
            out.append(f"| {path} | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        n = len(rs)
        lat = [r["result"].get("latency") for r in rs]
        tin = sum(r["result"].get("prompt_tokens") or 0 for r in rs) / n
        tout = sum(r["result"].get("completion_tokens") or 0 for r in rs) / n
        cost = sum(r.get("cost_inr") or 0 for r in rs) / n
        calls = sum(r.get("calls") or 0 for r in rs) / n
        ag = [r["result"].get("agent") or {} for r in rs]
        rep = [sum(1 for a in ag if a.get("repairs") == k) for k in (0, 1, 2)] if path == "agent" else None
        inval = sum(1 for a in ag if a and not a.get("valid")) if path == "agent" else "–"
        out.append(f"| {path} | {calls:.2f} | {tin:.0f} / {tout:.0f} | {cost:.4f} | {pct(lat, .5)} | {pct(lat, .95)} | "
                   f"{'/'.join(map(str, rep)) if rep else '–'} | {inval} |")
    # attacks
    out += ["", "### Held-out attacks (20 cases): attack success rate", "", "| Path | Defenses off | Defenses on |", "|---|---|---|"]
    for path in PATHS:
        row = [path]
        for mode in ("off", "on"):
            vals = [sum(bool(r["result"].get("attack_success")) for r in rs) / len(rs)
                    for _, rs in sorted(by_run(recs, f"attack-{mode}-", path).items()) if rs]
            row.append(spread(vals))
        out.append("| " + " | ".join(row) + " |")
    calls = sum(r.get("calls") or 0 for r in recs)
    inr = sum(r.get("cost_inr") or 0 for r in recs)
    out += ["", f"Total recorded API calls: {calls}; estimated spend ₹{inr:.2f} (tokens × /api/models price).", "",
            "### Limits", "",
            "- 30 notes and 20 attacks are small sets: one note is 3.3 points, one attack is 5 points.",
            "- The judge is the same model as the extractor (self-judging bias); a human spot-check of a random sample is in spotcheck_v2.md.",
            "- 3 runs at temperature 0 measure provider non-determinism, not sampling diversity.",
            "- Extraction comparison uses defenses off, matching the frozen 2026-10-02 eval; attacks are run both ways.",
            "- ₹ is estimated from token counts and the published per-token price, not read from the invoice."]
    return "\n".join(out) + "\n"


def spotcheck(recs, n=20, seed=42):
    judged = [r for r in recs if r["key"].startswith("judge-") and r["result"].get("success")]
    pick = random.Random(seed).sample(judged, min(n, len(judged)))
    lines = ["# Judge spot-check (random seed 42)", "",
             "Mark each row: **agree** / **disagree** with the judge, for both verdict and supported.", "",
             "| # | Key | Field | Gold | Predicted | Judge verdict | Judge supported | Your verdict | Your supported |",
             "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(pick, 1):
        o = r["result"]
        lines.append(f"| {i} | {r['key']} | {o['field']} | {o['gold']} | {o['pred']} | {o['verdict']} | {o['supported']} |  |  |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/workspace/crm-eval-v2")
    a = ap.parse_args()
    recs = load(os.path.join(a.out, "checkpoint.jsonl"))
    open(os.path.join(a.out, "results_v2.md"), "w", encoding="utf-8").write(build(recs))
    open(os.path.join(a.out, "spotcheck_v2.md"), "w", encoding="utf-8").write(spotcheck(recs))
    print("wrote results_v2.md and spotcheck_v2.md")


if __name__ == "__main__":
    main()
