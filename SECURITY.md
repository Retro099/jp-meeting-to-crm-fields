# Security

## Threat model
A sales rep pastes a meeting note. The note may contain text written by someone else (an email quoted from a customer,
a forwarded chat). That text can try to steer the model: **indirect prompt injection, OWASP LLM01:2025**.
What an attacker wants here: wrong or malicious CRM values, extra JSON keys or markup that downstream systems trust,
or a leak of the system prompt / secrets.

## Defenses (off by default)
Turn them on with the **🛡️ Security defenses** switch in the app sidebar, or set `DEFENSES_ENABLED=1`. Code: `crm_extractor/security.py`, wired in `crm_extractor/extractor.py`.

| Layer | What it does |
| :--- | :--- |
| Spotlighting | The note is wrapped in random `<<NOTE_xxxx>>` delimiters, followed by a one-line rule that text inside is data, never instructions. Fake copies of the delimiter are removed. The original system prompt is not changed. |
| Canary scan | A random secret is planted in the system prompt; if it appears in the output, the whole result is blocked. |
| Schema validation | Values must be short (≤200 chars), single-line plain text; nested objects are rejected. |
| Field allowlist | Only the five CRM keys survive; the raw JSON shown to users is the cleaned one. |
| Instruction-like refusal | Values that look like instructions, roles, links, HTML/code or braces become `未検出`. |
| Provenance check (no AI calls) | Each value is compared with the note after normalizing (NFKC full/half width, lower case, `(株)`→`株式会社`, no spaces, punctuation or common particles; honorifics like 様/さん dropped; several contacts checked one by one). 会社名/相手/期限: not found → **flag**; less than half of the value's 2-character pieces found → **block** (`未検出`). 次アクション/リスク are summaries, so they are only **flagged** when under half matches, never blocked. `未検出` is always allowed. |
| Input note scan (display only, no AI calls) | `scan_note_for_injection` looks for instruction-like lines (EN + JA, e.g. `システム：`, "ignore previous instructions") in the pasted note and shows them in the panel: red "NOT neutralized" with defenses off, yellow "ignored by defenses" with defenses on. It does not change the extracted fields. It flags 40/40 notes in `data/attacks_v1.jsonl` and 0/35 clean notes (`gold_30` + `missing_5`), but the patterns were written while looking at that attack set, so this is a sanity check, not a detection rate on new attacks. |

When defenses are on, the app shows a security panel with every block or flag and the reason, and a clear message if the canary check blocked the answer.

## Results
See [`eval/security_results.md`](eval/security_results.md). Defenses off: 18/40 attacks succeeded (45.0%, one run).
Defenses on, 3 runs: attack success 7.5% / 5.0% / 7.5% (mean 6.7%); exact match 60.0% / 60.7% / 62.0% (mean 60.9%) vs 60.0% off.
Provenance flagged 8 of 450 correct-set values (1.8%) and blocked none.

## How to test it yourself
- In the app: switch defenses on, paste a note from [`docs/SECURITY_DEMO.md`](docs/SECURITY_DEMO.md), compare with defenses off.
- Offline, free: `pytest -q tests/test_security.py tests/test_app_smoke.py`.
- Full measurement (uses API credits, 70 calls per repeat): the **Security eval** workflow, or the commands in the README.

## Limits
Pattern filters cannot judge meaning: an injected value that looks normal (e.g. 「全額返金の手続き」) still gets through.
The provenance check does not help there either, because the attacker writes that value into the note itself, so it *is* "in the note".
A001 (hidden instruction) and A032 (role spoofing) succeeded in all 3 defended runs; A031 in 2 of 3.
Keep a human review step before saving to the CRM. Results are 3 temperature-0 runs on a small synthetic dataset.

## Reporting
Please open a GitHub issue (no secrets or personal data) or contact the maintainer via the GitHub profile.
