"""Timeout -> fallback path of extract_with_fallback, with a mocked client (no network)."""
import json
from types import SimpleNamespace

import httpx
import openai

from crm_extractor import extractor
from crm_extractor.prompts import MODEL_NAME

GOOD = {"会社名": "株式会社テスト", "相手": "山田", "次アクション": "資料送付", "期限": "金曜", "リスク": "予算"}


class Client:
    """Fails the first create() with `first_exc`, answers later calls. Records model and options."""

    def __init__(self, first_exc=None):
        self.calls, self.options = [], []
        self._first_exc = first_exc
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def with_options(self, **opts):
        self.options.append(opts)
        return self

    def _create(self, **kw):
        self.calls.append(kw["model"])
        if self._first_exc is not None and len(self.calls) == 1:
            raise self._first_exc
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(GOOD)))],
                               usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2))


REQ = httpx.Request("POST", "https://example.invalid/v1/chat/completions")


def test_primary_ok_no_fallback():
    c = Client()
    r = extractor.extract_with_fallback(c, "note", defenses=False, fallback_model="fb/model")
    assert r["success"] and r["model"] == MODEL_NAME and r["fallback_used"] is False
    assert c.calls == [MODEL_NAME]
    assert c.options[0]["timeout"] == 25 and c.options[0]["max_retries"] == 0


def test_timeout_goes_to_fallback_once():
    c = Client(first_exc=openai.APITimeoutError(request=REQ))
    r = extractor.extract_with_fallback(c, "note", defenses=False, fallback_model="fb/model")
    assert c.calls == [MODEL_NAME, "fb/model"]
    assert r["success"] and r["model"] == "fb/model" and r["fallback_used"] is True
    assert r["data"]["会社名"] == "株式会社テスト"


def test_rate_limit_does_not_fall_back():
    resp = httpx.Response(429, request=REQ)
    c = Client(first_exc=openai.RateLimitError("Error code: 429", response=resp, body=None))
    r = extractor.extract_with_fallback(c, "note", defenses=False, fallback_model="fb/model")
    assert c.calls == [MODEL_NAME]
    assert not r["success"] and r["fallback_used"] is False


def test_fallback_off_when_empty():
    c = Client(first_exc=openai.APITimeoutError(request=REQ))
    r = extractor.extract_with_fallback(c, "note", defenses=False, fallback_model="")
    assert c.calls == [MODEL_NAME] and not r["success"] and r["timed_out"]
