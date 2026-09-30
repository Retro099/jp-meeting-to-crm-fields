import json
from types import SimpleNamespace

import judge


class FakeClient:
    def __init__(self, content):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._content = content

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))],
                               usage=SimpleNamespace(prompt_tokens=300, completion_tokens=25, total_tokens=325))


def test_prompt_file_has_placeholders_and_json_contract():
    template = judge.load_prompt()
    for ph in ["<<FIELD>>", "<<NOTE>>", "<<GOLD>>", "<<PRED>>"]:
        assert ph in template
    assert '"verdict"' in template and "match" in template and "partial" in template and "miss" in template


def test_build_judge_prompt_fills_all_placeholders():
    p = judge.build_judge_prompt(judge.load_prompt(), "リスク", "メモ本文", "予算不足", "")
    assert "<<" not in p
    assert "予算不足" in p and "メモ本文" in p and "(空 / empty)" in p


def test_judge_one_parses_verdict_with_mock_client():
    client = FakeClient(json.dumps({"verdict": "partial", "reason": "one of two risks"}))
    parsed, latency, tokens = judge.judge_one(client, judge.load_prompt(), "リスク", "メモ", "A、B", "A")
    assert parsed == {"verdict": "partial", "reason": "one of two risks"}
    assert tokens == (300, 25)
    assert client.calls[0]["temperature"] == 0
    assert client.calls[0]["model"] == judge.MODEL_NAME
