# Security

## Threat model
A sales rep pastes a meeting note. The note may contain text written by someone else (an email quoted from a customer,
a forwarded chat). That text can try to steer the model: **indirect prompt injection, OWASP LLM01:2025**.
What an attacker wants here: wrong or malicious CRM values, extra JSON keys or markup that downstream systems trust,
or a leak of the system prompt / secrets.

## Defenses (off by default)
Set `DEFENSES_ENABLED=1` to turn them on. Code: `security.py`, wired in `extractor.py`.

| Layer | What it does |
| :--- | :--- |
| Spotlighting | The note is wrapped in random `<<NOTE_xxxx>>` delimiters and the system prompt says text inside is data, never instructions. Fake copies of the delimiter are removed. |
| Canary scan | A random secret is planted in the system prompt; if it appears in the output, the whole result is blocked. |
| Schema validation | Values must be short (≤200 chars), single-line plain text; nested objects are rejected. |
| Field allowlist | Only the five CRM keys survive; the raw JSON shown to users is the cleaned one. |
| Instruction-like refusal | Values that look like instructions, roles, links, HTML/code or braces become `未検出`. |

## Results
See [`eval/security_results.md`](eval/security_results.md): attack success rate 45.0% → 10.0% on 40 cases; exact match with defenses on 59.3% (89/150), 1 field below the 60.0% target.

## Limits
Pattern filters cannot judge meaning: an injected value that looks normal (e.g. 「リスクなし」) still gets through.
Keep a human review step before saving to the CRM. Results are a single temperature-0 run on a synthetic dataset.

## Reporting
Please open a GitHub issue (no secrets or personal data) or contact the maintainer via the GitHub profile.
