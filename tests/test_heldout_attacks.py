import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "eval"))


def _cases():
    with open(os.path.join(ROOT, "data", "attacks_v2_heldout.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_heldout_set_shape():
    cases = _cases()
    assert len(cases) == 20
    assert len({c["id"] for c in cases}) == 20
    cats = {c["category"] for c in cases}
    assert cats == {"hidden_instruction", "canary_leak", "format_break", "role_spoofing", "field_poisoning"}
    for cat in cats:
        langs = [c["lang"] for c in cases if c["category"] == cat]
        assert sorted(langs) == ["en", "en", "ja", "ja"]


def test_heldout_markers_not_reused_from_v1():
    with open(os.path.join(ROOT, "data", "attacks_v1.jsonl"), encoding="utf-8") as f:
        v1 = {json.loads(line)["success"].get("marker") for line in f if line.strip()}
    for c in _cases():
        assert c["success"].get("marker") not in v1 - {None}


def test_new_run_dir_respects_env(tmp_path, monkeypatch):
    import paths
    monkeypatch.setenv("EVAL_RUN_DIR", str(tmp_path / "x"))
    assert paths.new_run_dir() == str(tmp_path / "x")
    assert os.path.isdir(tmp_path / "x")
