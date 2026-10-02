import pytest

from scoring import (FIELDS, JUDGED_FIELDS, VERDICT_POINTS, exact_match, overall, parse_verdict,
                     score_exact, summarize_verdicts)


def test_exact_match_trims_whitespace_only():
    assert exact_match("明日中", " 明日中 ")
    assert not exact_match("明日中", "明日")
    assert not exact_match("オンプレ版の構成案を提出", "オンプレ版の構成案の提出")


def test_exact_match_handles_none():
    assert exact_match(None, "")
    assert not exact_match(None, "x")


def test_score_exact_counts_per_field_and_overall():
    gold = {"会社名": "A社", "相手": "田中", "次アクション": "資料の送付", "期限": "明日", "リスク": "予算"}
    pred = dict(gold, リスク="予算不足")
    scores = score_exact([(gold, pred), (gold, {})])
    assert scores["会社名"] == {"correct": 1, "total": 2}
    assert scores["リスク"] == {"correct": 0, "total": 2}
    assert overall(scores) == (4, 10)
    assert set(scores) == set(FIELDS)


def test_verdict_points():
    assert VERDICT_POINTS == {"match": 1.0, "partial": 0.5, "miss": 0.0}
    assert JUDGED_FIELDS == ["次アクション", "リスク"]


@pytest.mark.parametrize("text,verdict", [
    ('{"verdict": "match", "reason": "same meaning"}', "match"),
    ('```json\n{"verdict": "Partial", "reason": "one of two risks"}\n```', "partial"),
    ('  {"verdict": "miss"}  ', "miss"),
])
def test_parse_verdict_ok(text, verdict):
    parsed = parse_verdict(text)
    assert parsed["verdict"] == verdict
    assert isinstance(parsed["reason"], str)


@pytest.mark.parametrize("text", ["not json", '["match"]', '{"verdict": "yes"}', "", None])
def test_parse_verdict_rejects_bad_output(text):
    with pytest.raises(ValueError):
        parse_verdict(text)


def test_summarize_verdicts():
    s = summarize_verdicts(["match", "partial", "miss", "match"])
    assert s["n"] == 4
    assert s["counts"] == {"match": 2, "partial": 1, "miss": 1}
    assert s["semantic_score"] == pytest.approx(2.5 / 4)
    assert s["strict_match_rate"] == pytest.approx(0.5)
    assert summarize_verdicts([])["semantic_score"] == 0.0


def test_inr_estimate():
    import report
    # 1M input + 1M output tokens at $0.36 + $0.40, x1.05 x1.05 fees, at 100 INR/USD
    assert report.inr_estimate(1_000_000, 1_000_000, 100) == pytest.approx(0.76 * 1.1025 * 100)


def test_score_not_found():
    from scoring import score_not_found
    gold = {"会社名": "株式会社A", "相手": "未検出", "次アクション": "見積の送付", "期限": "未検出", "リスク": "競合"}
    pred = {"会社名": "未検出", "相手": "未検出", "次アクション": "見積の送付", "期限": "来週", "リスク": "競合"}
    assert score_not_found([(gold, pred)]) == {"absent_total": 2, "absent_correct": 1,
                                                "present_total": 3, "false_not_found": 1}


def test_run_eval_output_paths():
    import run_eval
    pred, meta = run_eval.output_paths()
    assert pred.endswith("predictions_t0.jsonl") and meta.endswith("run_meta_t0.json")
    pred, meta = run_eval.output_paths("missing5")
    assert pred.endswith("predictions_missing5.jsonl") and meta.endswith("run_meta_missing5.json")


def test_missing_5_set_is_consistent():
    import json
    import os
    from scoring import FIELDS, NOT_FOUND
    path = os.path.join(os.path.dirname(__file__), "..", "data", "missing_5.jsonl")
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    assert len(rows) == 5
    for r in rows:
        assert set(r["expected"]) == set(FIELDS)
        absent = sorted(k for k, v in r["expected"].items() if v == NOT_FOUND)
        assert absent == sorted(r["missing"]) and 1 <= len(absent) <= 2
