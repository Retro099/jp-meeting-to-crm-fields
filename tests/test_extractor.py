import json
from types import SimpleNamespace

import pytest

import extractor
from prompts import MODEL_NAME, SYSTEM_PROMPT, TEMPERATURE


class FakeClient:
    """Minimal stand-in for openai.OpenAI (no network)."""

    def __init__(self, content=None, exc=None):
        self.calls = []
        self._content, self._exc = content, exc
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc:
            raise self._exc
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120),
        )


GOOD = {"会社名": "株式会社フロントライン", "相手": "高橋", "次アクション": "API仕様書の送付",
        "期限": "今月末", "リスク": "先方エンジニアリソース不足"}


def test_success_uses_shared_settings():
    client = FakeClient(json.dumps(GOOD, ensure_ascii=False))
    result = extractor.extract_crm_data(client, "メモ")
    assert result["success"] and result["data"] == GOOD
    assert result["total_tokens"] == 120 and result["latency"] >= 0
    call = client.calls[0]
    assert call["model"] == MODEL_NAME and call["temperature"] == TEMPERATURE
    assert call["response_format"] == {"type": "json_object"}
    assert call["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert call["messages"][1]["content"].endswith("メモ")


@pytest.mark.parametrize("content", ["not json", "[1, 2]", None])
def test_bad_json_is_reported_not_raised(content):
    result = extractor.extract_crm_data(FakeClient(content), "メモ")
    assert not result["success"] and "JSON" in result["error"]


def test_api_error_is_reported_not_raised():
    result = extractor.extract_crm_data(FakeClient(exc=RuntimeError("boom")), "メモ")
    assert not result["success"] and "boom" in result["error"]


def test_parse_json_object():
    assert extractor.parse_json_object('{"a": 1}') == {"a": 1}
    with pytest.raises(ValueError):
        extractor.parse_json_object('"text"')
