"""Smoke tests for the Streamlit UI (app.py) with a monkeypatched OpenAI client: no network, no real key."""

import json
from types import SimpleNamespace

import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from ui_strings import STRINGS  # noqa: E402

MODEL_OUTPUT = {"会社名": "株式会社フロントライン", "相手": "高橋", "次アクション": "API仕様書の送付",
                "期限": "未検出", "リスク": "先方エンジニアリソース不足"}
NOTE = "打ち合わせ記録：(株)フロントライン 高橋様。API仕様書をこっちでまとめて送る。"


class FakeOpenAI:
    calls = 0

    def __init__(self, **kwargs):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        FakeOpenAI.calls += 1
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(MODEL_OUTPUT, ensure_ascii=False)))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120),
        )


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("AICREDITS_API_KEY", "test-dummy-key")
    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    FakeOpenAI.calls = 0
    streamlit.cache_resource.clear()
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception
    return at


def _texts(at):
    return [c.value for c in at.caption] + [m.value for m in at.markdown]


def test_japanese_default_with_privacy_note(app):
    assert app.radio(key="lang").value == "ja"
    assert app.title[0].value == STRINGS["ja"]["title"]
    assert app.button[0].label == STRINGS["ja"]["run_button"]
    assert STRINGS["ja"]["privacy_note"] in _texts(app)


def test_switch_to_english(app):
    app.radio(key="lang").set_value("en").run()
    assert not app.exception
    assert app.title[0].value == STRINGS["en"]["title"]
    assert STRINGS["en"]["privacy_note"] in _texts(app)


def test_empty_note_warning(app):
    app.button[0].click().run()
    assert app.warning[0].value == STRINGS["ja"]["empty_note"]
    assert FakeOpenAI.calls == 0


def test_extract_then_edit_fields(app):
    app.text_area(key="note_input").set_value(NOTE)
    app.button[0].click().run()
    assert not app.exception and FakeOpenAI.calls == 1
    assert app.text_input(key="edit_会社名").value == "株式会社フロントライン"
    assert app.text_input(key="edit_期限").value == "未検出"   # shown as-is
    assert app.text_area(key="edit_リスク").value == "先方エンジニアリソース不足"
    app.text_input(key="edit_期限").set_value("今月末").run()
    assert not app.exception and FakeOpenAI.calls == 1      # editing does not call the API again
    edited = json.loads(app.code[0].value)
    assert edited == {**MODEL_OUTPUT, "期限": "今月末"}
    assert len(app.get("download_button")) == 1


def test_session_cap(app):
    app.text_area(key="note_input").set_value(NOTE)
    for _ in range(5):
        app.button[0].click().run()
    assert FakeOpenAI.calls == 5
    app.button[0].click().run()
    assert FakeOpenAI.calls == 5
    assert STRINGS["ja"]["session_limit"].format(max_runs=5) in [w.value for w in app.warning]


def test_missing_key_message(monkeypatch):
    monkeypatch.delenv("AICREDITS_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception
    assert "AICREDITS_API_KEY" in at.error[0].value
