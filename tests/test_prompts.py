import prompts


def test_model_settings():
    assert prompts.MODEL_NAME == "qwen/qwen-2.5-72b-instruct"
    assert prompts.API_BASE_URL.startswith("https://")
    assert prompts.TEMPERATURE == 0


def test_system_prompt_lists_all_fields():
    for field in ["会社名", "相手", "次アクション", "期限", "リスク"]:
        assert field in prompts.SYSTEM_PROMPT
    assert "JSON" in prompts.SYSTEM_PROMPT


def test_not_found_rule_in_prompt():
    assert prompts.NOT_FOUND == "未検出"
    assert "「未検出」" in prompts.SYSTEM_PROMPT
    assert "推測" in prompts.SYSTEM_PROMPT


def test_crm_fields_order():
    assert prompts.CRM_FIELDS == ["会社名", "相手", "次アクション", "期限", "リスク"]


def test_scoring_uses_same_not_found_marker():
    import scoring
    assert scoring.NOT_FOUND == prompts.NOT_FOUND
