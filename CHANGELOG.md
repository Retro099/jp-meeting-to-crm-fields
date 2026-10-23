# Changelog

## [Unreleased]

### Added
- Optional, experimental LangGraph agent (`crm_extractor/agent.py`): extract -> validate -> repair (max 2 retries, re-prompted with the validation errors) -> done. Reuses the shared prompt, message builders, JSON parsing and `security.validate_schema`. Results carry an `agent` block (`calls`, `repairs`, `errors`, `valid`).
- Off-by-default "LangGraph agent (experimental)" toggle in the Streamlit sidebar.
- `tests/test_agent.py`: mocked-LLM tests (valid first try, invalid then repaired, repaired on 2nd retry, invalid 3 times -> errors flagged, defenses on).
- `eval/safe_runner.py`: fail-safe runner for future paid batches. JSONL checkpoint after every call (key run|path|note|field) with resume; 402 / insufficient-balance / quota stops at once (exit 3); plain 429 gets one backoff retry then stops (exit 4); hard caps 2,000 calls, 400 calls/day (IST), ₹100 spend (exit 2); pre-batch `GET /api/credits` balance check that stops while a ₹20 buffer remains for the live demo (exit 5). `tests/test_safe_runner.py` (10 mocked tests).
- Eval v2 harness (`eval/eval_v2.py`, `eval/judge_v2_prompt.txt`): same-session comparison of the old path vs the agent on gold_30 (3 runs each, temperature 0), exact match + per-field judge (verdict + supported-by-note), repairs, tokens, ₹/note, p50/p95 latency, and held-out 20 attacks (defenses off/on, both paths, 3 runs). Queue order: extraction, attacks, judge. Runs through `safe_runner` with exact per-request call counting.
- `scripts/eval_v2_driver.sh`: detached driver that pauses at the 400/day cap until 00:05 IST and resumes from the checkpoint; writes STATUS.json on finish/stop; `--watchdog` mode for cron.
- `eval/report_v2.py`: checkpoint -> results tables + limits, and a 20-row judge spot-check sheet (seed 42). Numbers are not in the README yet.
- `safe_runner`: balance URL changed to `GET /api/credits` (the documented `/v1/credits` returns 404); daily cap is its own exit code (6) and accounts for the agent's worst case of 3 calls per item.
- `langgraph==1.2.16` pinned in `requirements.txt`.

### Unchanged
- `extract_crm_data` stays the default path; prompt and frozen eval untouched. No new eval numbers yet (no API calls made).

## [1.0.0] - 2026-10
- First release (see GitHub release v1.0.0).
