# Changelog

## [Unreleased]

### Added
- Optional, experimental LangGraph agent (`crm_extractor/agent.py`): extract -> validate -> repair (max 1 retry, re-prompted with the validation errors) -> done. Reuses the shared prompt, message builders, JSON parsing and `security.validate_schema`. Results carry an `agent` block (`calls`, `repairs`, `errors`, `valid`).
- Off-by-default "LangGraph agent (experimental)" toggle in the Streamlit sidebar.
- `tests/test_agent.py`: mocked-LLM tests (valid first try, invalid then repaired, invalid twice -> errors flagged, defenses on).
- `langgraph==1.2.16` pinned in `requirements.txt`.

### Unchanged
- `extract_crm_data` stays the default path; prompt and frozen eval untouched. No new eval numbers yet (no API calls made).

## [1.0.0] - 2026-10
- First release (see GitHub release v1.0.0).
