"""LangGraph agent with a mocked LLM (no network, no API key)."""

import json
from types import SimpleNamespace

from crm_extractor.agent import extract_crm_data_agent
from crm_extractor.prompts import NOT_FOUND

GOOD = {"会社名": "株式会社テスト", "相手": "山田", "次アクション": "見積の送付", "期限": "今月末", "リスク": "予算"}


class FakeClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw["messages"])
        content = self.outputs.pop(0)
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage)


def test_valid_first_try():
    c = FakeClient([json.dumps(GOOD, ensure_ascii=False)])
    r = extract_crm_data_agent(c, "メモ", defenses=False)
    assert r["success"] and r["data"] == GOOD
    assert r["agent"] == {"calls": 1, "repairs": 0, "errors": [], "valid": True}
    assert r["total_tokens"] == 15


def test_invalid_then_repaired():
    bad = {k: v for k, v in GOOD.items() if k != "期限"}
    c = FakeClient([json.dumps(bad, ensure_ascii=False), json.dumps(GOOD, ensure_ascii=False)])
    r = extract_crm_data_agent(c, "メモ", defenses=False)
    assert r["success"] and r["agent"]["valid"] and r["agent"]["repairs"] == 1 and r["agent"]["calls"] == 2
    assert "missing key: 期限" in c.calls[1][-1]["content"]  # repair prompt carries the validation errors
    assert r["total_tokens"] == 30


def test_invalid_twice_returns_errors_flagged():
    c = FakeClient(["not json", "still not json"])
    r = extract_crm_data_agent(c, "メモ", defenses=False)
    assert not r["success"] and r["agent"]["calls"] == 2 and not r["agent"]["valid"]
    assert r["agent"]["errors"]


def test_schema_problem_twice_flagged_but_fields_returned():
    bad = dict(GOOD, リスク="一行目\n二行目")
    c = FakeClient([json.dumps(bad, ensure_ascii=False)] * 2)
    r = extract_crm_data_agent(c, "メモ", defenses=False)
    assert r["success"] and not r["agent"]["valid"] and r["agent"]["calls"] == 2
    assert any("multi-line" in e for e in r["agent"]["errors"])


def test_defenses_on_runs_harden_output():
    c = FakeClient([json.dumps(GOOD, ensure_ascii=False)])
    r = extract_crm_data_agent(c, "株式会社テストの山田様。見積の送付、今月末。リスクは予算。", defenses=True)
    assert r["success"] and "security" in r
    assert set(r["data"]) == set(GOOD) and all(v for v in r["data"].values()) and NOT_FOUND
