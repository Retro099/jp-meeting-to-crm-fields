import prompts


def test_model_settings():
    assert prompts.MODEL_NAME == "qwen/qwen-2.5-72b-instruct"
    assert prompts.API_BASE_URL.startswith("https://")
    assert prompts.TEMPERATURE == 0


def test_system_prompt_lists_all_fields():
    for field in ["会社名", "相手", "次アクション", "期限", "リスク"]:
        assert field in prompts.SYSTEM_PROMPT
    assert "JSON" in prompts.SYSTEM_PROMPT
