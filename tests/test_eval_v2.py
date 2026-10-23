"""Eval v2 harness with a mocked LLM and mocked balance (no network)."""

import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))
import eval_v2 as ev  # noqa: E402
import report_v2 as rp  # noqa: E402
import safe_runner as sr  # noqa: E402

GOOD = {"会社名": "株式会社A", "相手": "田中", "次アクション": "見積の送付", "期限": "来週", "リスク": "予算"}
JUDGE = json.dumps({"verdict": "match", "supported": True, "reason": "ok"})


class FakeLLM:
    def __init__(self, fail_at=None, err="Error code: 402 - insufficient balance"):
        self.n, self.fail_at, self.err = 0, fail_at, err
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.n += 1
        if self.fail_at and self.n >= self.fail_at:
            raise Exception(self.err)
        text = kw["messages"][-1]["content"]
        content = JUDGE if "採点する評価者" in text else json.dumps(GOOD, ensure_ascii=False)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
                               usage=SimpleNamespace(prompt_tokens=600, completion_tokens=60, total_tokens=660))


@pytest.fixture
def small(monkeypatch, tmp_path):
    gold = tmp_path / "g.jsonl"
    gold.write_text("\n".join(json.dumps({"input": f"メモ{i}", "expected": GOOD}, ensure_ascii=False) for i in range(2)), encoding="utf-8")
    att = tmp_path / "a.jsonl"
    att.write_text(json.dumps({"id": "H1", "category": "c", "lang": "ja", "input": "x", "success": {"type": "canary"}}), encoding="utf-8")
    monkeypatch.setattr(ev, "GOLD", str(gold))
    monkeypatch.setattr(ev, "ATTACKS", str(att))
    return tmp_path


def run(tmp, llm, **caps):
    meter = ev.Meter(llm)
    call = ev.make_caller(meter, meter, pause=0)
    return ev.run_all(call, str(tmp / "checkpoint.jsonl"), balance=lambda: 50.0, sleep=lambda s: None, **caps), meter


def test_full_plan_order_counts_and_report(small):
    out, meter = run(small, FakeLLM())
    recs = rp.load(str(small / "checkpoint.jsonl"))
    kinds = [r["key"].split("-")[0] for r in recs]
    assert kinds == sorted(kinds, key=["extract", "attack", "judge"].index)  # cheapest sections first
    # 2 notes x 2 paths x 3 runs + 1 attack x 2 modes x 2 paths x 3 runs + 12 extractions x 5 fields
    assert len(recs) == 12 + 12 + 60 and meter.calls == 84
    assert all(r["cost_inr"] > 0 for r in recs)
    md = rp.build(recs)
    assert "1.000 ± 0.000" in md and "0/2 notes gave different outputs" in md
    sheet = rp.spotcheck(recs)
    assert sheet.count("| judge-") == 20


def test_402_mid_run_stops_and_resume_completes(small):
    with pytest.raises(sr.StopRun) as e:
        run(small, FakeLLM(fail_at=5))
    assert e.value.code == sr.EXIT_BILLING
    assert len(rp.load(str(small / "checkpoint.jsonl"))) == 4
    out, meter = run(small, FakeLLM())
    assert meter.calls == 80  # only the missing items are called again


def test_429_twice_stops_rate(small):
    with pytest.raises(sr.StopRun) as e:
        run(small, FakeLLM(fail_at=1, err="Error code: 429 - rate limit"))
    assert e.value.code == sr.EXIT_RATE


def test_daily_cap_uses_worst_case_agent_calls(small):
    with pytest.raises(sr.StopRun) as e:
        run(small, FakeLLM(), per_day=8)
    assert e.value.code == sr.EXIT_DAY


def test_balance_low_stops_before_calls(small):
    llm = FakeLLM()
    meter = ev.Meter(llm)
    with pytest.raises(sr.StopRun) as e:
        ev.run_all(ev.make_caller(meter, meter, pause=0), str(small / "checkpoint.jsonl"), balance=lambda: 19.5, buffer_inr=20)
    assert e.value.code == sr.EXIT_BALANCE and llm.n == 0


def test_status_file(small):
    run(small, FakeLLM())
    st = ev.write_status(str(small), "done", "ok", (0, 0.0), 50.0)
    saved = json.load(open(small / "STATUS.json"))
    assert saved["state"] == "done" and saved["calls"] == 84 and set(saved["per_step"]) == {"extract", "attack", "judge"}
    assert st["inr_spent_est"] > 0


def test_next_0005():
    now = ev.datetime.datetime(2026, 10, 23, 18, 0, tzinfo=ev.IST)
    assert ev.seconds_to_next_0005(now) == 6 * 3600 + 5 * 60


def test_real_plan_size_fits_caps():
    gold, att = ev.load_jsonl(ev.GOLD), ev.load_jsonl(ev.ATTACKS)
    n_ex, n_at = len(ev.extract_items(gold)), len(ev.attack_items(att))
    assert (n_ex, n_at) == (180, 240)
    assert n_ex + n_at + n_ex * 5 <= sr.DEFAULT_MAX_CALLS - 100
