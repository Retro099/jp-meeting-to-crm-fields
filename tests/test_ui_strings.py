import re

import pytest

from demo_limits import MAX_CHARS, MAX_RUNS_PER_SESSION, reserve_run, validate_note
from prompts import CRM_FIELDS
from ui_strings import DEFAULT_LANG, LANG_LABELS, STRINGS, t


def test_japanese_is_default_and_both_languages_exist():
    assert DEFAULT_LANG == "ja"
    assert set(STRINGS) == set(LANG_LABELS) == {"ja", "en"}


def test_both_languages_have_the_same_keys():
    assert set(STRINGS["ja"]) == set(STRINGS["en"])


@pytest.mark.parametrize("key", sorted(STRINGS["ja"]))
def test_same_placeholders_and_non_empty(key):
    def placeholders(s):
        return set(re.findall(r"{(\w+)}", s))
    assert STRINGS["ja"][key].strip() and STRINGS["en"][key].strip()
    assert placeholders(STRINGS["ja"][key]) == placeholders(STRINGS["en"][key])


def test_every_field_has_a_label():
    for lang in STRINGS:
        for f in CRM_FIELDS:
            assert f in t(lang, f"field_{f}")


def test_privacy_note_mentions_provider_in_both_languages():
    assert "AICredits" in t("ja", "privacy_note") and "機密" in t("ja", "privacy_note")
    assert "AICredits" in t("en", "privacy_note") and "confidential" in t("en", "privacy_note")


def test_unknown_language_falls_back_to_japanese():
    assert t("xx", "run_button") == STRINGS["ja"]["run_button"]


def test_limit_messages_in_japanese():
    assert validate_note("", lang="ja")[1] == STRINGS["ja"]["empty_note"]
    level, msg = validate_note("あ" * (MAX_CHARS + 1), lang="ja")
    assert level == "error" and str(MAX_CHARS) in msg and "文字" in msg
    allowed, msg, _ = reserve_run(MAX_RUNS_PER_SESSION, {}, "2026-10-02", lang="ja")
    assert not allowed and f"{MAX_RUNS_PER_SESSION} 回" in msg
    allowed, msg, _ = reserve_run(0, {"2026-10-02": 50}, "2026-10-02", lang="ja")
    assert not allowed and "上限" in msg
