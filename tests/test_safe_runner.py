"""Fail-safe eval runner with mocked calls/HTTP (no network)."""

import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))
import safe_runner as sr  # noqa: E402


class HTTPErr(Exception):
    def __init__(self, status, body=""):
        super().__init__(f"Error code: {status}")
        self.status_code, self.body = status, body


ITEMS = [(sr.make_key("r1", "agent", f"n{i}"), i) for i in range(3)]


def test_defaults_match_approved_limits():
    assert (sr.DEFAULT_MAX_CALLS, sr.DEFAULT_PER_DAY, sr.DEFAULT_MAX_SPEND_INR) == (2000, 400, 100.0)


def test_checkpoint_and_resume(tmp_path):
    cp = str(tmp_path / "cp.jsonl")
    seen = []

    def call(p):
        if p == 2 and len(seen) == 2 and not os.environ.get("_resumed"):
            raise HTTPErr(402, "insufficient balance")
        seen.append(p)
        return {"success": True}

    with pytest.raises(sr.StopRun) as e:
        sr.run_batch(ITEMS, call, cp, today="2026-10-24")
    assert e.value.code == sr.EXIT_BILLING and len(open(cp).readlines()) == 2
    os.environ["_resumed"] = "1"
    try:
        out = sr.run_batch(ITEMS, call, cp, today="2026-10-24")
    finally:
        del os.environ["_resumed"]
    assert out["skipped"] == 2 and out["made"] == 1 and seen == [0, 1, 2]


def test_402_stops_without_retry(tmp_path):
    calls = []

    def call(p):
        calls.append(p)
        raise HTTPErr(402)

    with pytest.raises(sr.StopRun) as e:
        sr.run_batch(ITEMS, call, str(tmp_path / "c.jsonl"), sleep=lambda s: None)
    assert e.value.code == sr.EXIT_BILLING and calls == [0]


def test_quota_body_on_429_is_billing(tmp_path):
    with pytest.raises(sr.StopRun) as e:
        sr.run_batch(ITEMS, lambda p: (_ for _ in ()).throw(HTTPErr(429, "quota exceeded")), str(tmp_path / "c.jsonl"))
    assert e.value.code == sr.EXIT_BILLING


def test_429_one_backoff_then_ok(tmp_path):
    state = {"n": 0}
    sleeps = []

    def call(p):
        state["n"] += 1
        if state["n"] == 1:
            raise HTTPErr(429, "rate limit")
        return {"success": True}

    out = sr.run_batch(ITEMS[:1], call, str(tmp_path / "c.jsonl"), sleep=sleeps.append)
    assert out["made"] == 1 and len(sleeps) == 1 and out["total_calls"] == 2


def test_429_twice_stops(tmp_path):
    with pytest.raises(sr.StopRun) as e:
        sr.run_batch(ITEMS, lambda p: (_ for _ in ()).throw(HTTPErr(429, "rate limit")), str(tmp_path / "c.jsonl"), sleep=lambda s: None)
    assert e.value.code == sr.EXIT_RATE


def test_max_calls_and_per_day(tmp_path):
    with pytest.raises(sr.StopRun, match="Hard cap"):
        sr.run_batch(ITEMS, lambda p: {}, str(tmp_path / "a.jsonl"), max_calls=2)
    with pytest.raises(sr.StopRun, match="Daily pace") as e:
        sr.run_batch(ITEMS, lambda p: {}, str(tmp_path / "b.jsonl"), per_day=1)
    assert e.value.code == sr.EXIT_DAY


def test_spend_cap(tmp_path):
    with pytest.raises(sr.StopRun, match="Spend cap"):
        sr.run_batch(ITEMS, lambda p: {"cost_inr": 60.0}, str(tmp_path / "s.jsonl"))


def fake_opener(payload):
    return lambda req, timeout=None: io.BytesIO(json.dumps(payload).encode())


def test_balance_low_stops_before_any_call(tmp_path):
    bal = sr.get_balance_inr("sk-test", opener=fake_opener({"data": {"total_credits": 0.1, "credits_inr": 12.0}}))
    assert bal == 12.0
    calls = []
    with pytest.raises(sr.StopRun) as e:
        sr.run_batch(ITEMS, calls.append, str(tmp_path / "c.jsonl"), balance=lambda: bal, buffer_inr=20)
    assert e.value.code == sr.EXIT_BALANCE and calls == []


def test_balance_alt_shape_and_unknown():
    assert sr.get_balance_inr("k", opener=fake_opener({"balance_inr": 245.5})) == 245.5
    assert sr.get_balance_inr("k", opener=fake_opener({"foo": 1})) is None
