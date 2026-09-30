"""Scoring helpers for the eval (pure functions, no network)."""

import json
import re

FIELDS = ["会社名", "相手", "次アクション", "期限", "リスク"]
JUDGED_FIELDS = ["次アクション", "リスク"]
VERDICT_POINTS = {"match": 1.0, "partial": 0.5, "miss": 0.0}


def exact_match(gold, pred):
    """Strict exact match after trimming whitespace (the metric used since iteration 1)."""
    return str(gold if gold is not None else "").strip() == str(pred if pred is not None else "").strip()


def score_exact(records, fields=FIELDS):
    """records: iterable of (expected_dict, predicted_dict). Returns {field: {"correct", "total"}}."""
    scores = {f: {"correct": 0, "total": 0} for f in fields}
    for expected, predicted in records:
        for f in fields:
            scores[f]["total"] += 1
            if exact_match(expected.get(f, ""), predicted.get(f, "")):
                scores[f]["correct"] += 1
    return scores


def overall(scores):
    correct = sum(s["correct"] for s in scores.values())
    total = sum(s["total"] for s in scores.values())
    return correct, total


def parse_verdict(text):
    """Parse the judge's JSON output into {"verdict", "reason"}. Raises ValueError if invalid."""
    if not isinstance(text, str):
        raise ValueError("judge output is not a string")
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"judge output is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("judge output is not a JSON object")
    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in VERDICT_POINTS:
        raise ValueError(f"unknown verdict: {data.get('verdict')!r}")
    return {"verdict": verdict, "reason": str(data.get("reason", "")).strip()}


def summarize_verdicts(verdicts):
    """verdicts: list of "match" / "partial" / "miss". Returns counts and scores."""
    n = len(verdicts)
    counts = {v: verdicts.count(v) for v in VERDICT_POINTS}
    points = sum(VERDICT_POINTS[v] for v in verdicts)
    return {
        "n": n,
        "counts": counts,
        "semantic_score": points / n if n else 0.0,   # match=1, partial=0.5, miss=0
        "strict_match_rate": counts["match"] / n if n else 0.0,  # match only
    }
