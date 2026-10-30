## Results v2 (same session, old path vs LangGraph agent)

Model qwen/qwen-2.5-72b-instruct, temperature 0, 30 gold notes, 3 runs per path. Mean ± std (min–max) over runs.

### Exact match per field

| Field | Old path | LangGraph agent |
|---|---|---|
| 会社名 | 0.967 ± 0.000 (0.967–0.967, n=3) | 0.956 ± 0.016 (0.933–0.967, n=3) |
| 相手 | 1.000 ± 0.000 (1.000–1.000, n=3) | 0.989 ± 0.016 (0.967–1.000, n=3) |
| 次アクション | 0.233 ± 0.000 (0.233–0.233, n=3) | 0.233 ± 0.000 (0.233–0.233, n=3) |
| 期限 | 0.789 ± 0.016 (0.767–0.800, n=3) | 0.744 ± 0.042 (0.700–0.800, n=3) |
| リスク | 0.000 ± 0.000 (0.000–0.000, n=3) | 0.000 ± 0.000 (0.000–0.000, n=3) |
| overall | 0.598 ± 0.003 (0.593–0.600, n=3) | 0.584 ± 0.014 (0.567–0.600, n=3) |

### LLM judge per field (match=1, partial=0.5, miss=0; supported = grounded in the note)

| Field | Old score | Agent score | Old supported | Agent supported |
|---|---|---|---|---|
| 会社名 | 0.983 ± 0.000 (0.983–0.983, n=3) | 0.983 ± 0.000 (0.983–0.983, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) |
| 相手 | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) |
| 次アクション | 0.889 ± 0.008 (0.883–0.900, n=3) | 0.899 ± 0.002 (0.897–0.900, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) |
| 期限 | 0.989 ± 0.008 (0.983–1.000, n=3) | 0.983 ± 0.000 (0.983–0.983, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) |
| リスク | 0.739 ± 0.016 (0.717–0.750, n=3) | 0.730 ± 0.022 (0.700–0.750, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) | 1.000 ± 0.000 (1.000–1.000, n=3) |

### Run-to-run variation at temperature 0

- old: 19/30 notes gave different outputs across runs.
- agent: 17/30 notes gave different outputs across runs.

### Cost, latency, repairs (extraction phase)

| Path | Calls/note | Tokens in/out per note | ₹ per note | p50 latency s | p95 latency s | Repairs (0/1/2) | Still invalid |
|---|---|---|---|---|---|---|---|
| old | 1.00 | 544 / 71 | 0.0224 | 4.59 | 9.51 | – | – |
| agent | 1.00 | 538 / 71 | 0.0221 | 4.75 | 11.57 | 89/0/0 | 0 |

### Held-out attacks (20 cases): attack success rate

| Path | Defenses off | Defenses on |
|---|---|---|
| old | 0.300 ± 0.000 (0.300–0.300, n=3) | 0.083 ± 0.024 (0.050–0.100, n=3) |
| agent | 0.300 ± 0.041 (0.250–0.350, n=3) | 0.100 ± 0.000 (0.100–0.100, n=3) |

Total recorded API calls: 1320; estimated spend ₹29.14 (tokens × /api/models price).

### Limits

- 30 notes and 20 attacks are small sets: one note is 3.3 points, one attack is 5 points.
- The judge is the same model as the extractor (self-judging bias); a human spot-check of 20 random judge grades (2026-10-30) agreed with the judge on 20/20 verdicts and 20/20 supported flags; small sample, see spotcheck_v2.md.
- 3 runs at temperature 0 measure provider non-determinism, not sampling diversity.
- Extraction comparison uses defenses off, matching the frozen 2026-10-02 eval; attacks are run both ways.
- ₹ is estimated from token counts and the published per-token price, not read from the invoice.
