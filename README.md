[![CI](https://github.com/Retro099/jp-meeting-to-crm-fields/actions/workflows/ci.yml/badge.svg)](https://github.com/Retro099/jp-meeting-to-crm-fields/actions/workflows/ci.yml)

[日本語版はこちら](README.ja.md)

# JP Meeting Note to CRM Fields Extractor

日本語の商談メモからCRM項目（相手・会社名・期限・次アクション・リスク）をLLMで抽出し、正解データで精度を評価するプロジェクトです。

**▶ Live demo: https://retro-jp-meeting-to-crm-fields.streamlit.app/**<br>
*It may be asleep if no one has used it recently. Click the wake-up button and wait a moment. Demo limits apply (see below).*

LLM extraction of CRM fields from unstructured Japanese business meeting notes, with a fixed 30-note exact-match evaluation. The prompt is designed for common patterns in Japanese business notes—corporate abbreviations, honorifics, and informal formatting—and uses Qwen 2.5 72B Instruct to return the fields as JSON.

The project includes a Streamlit frontend (runnable in Docker) that shows the extracted fields, request latency, and token usage for each run.

## 🎯 Why / Who it's for
Sales reps write quick, messy notes after a customer call, and then have to re-type the key facts into the CRM by hand. With this tool, a rep pastes the Japanese meeting note, gets the five CRM fields (相手・会社名・期限・次アクション・リスク) back as JSON, reviews and corrects them, and then saves them to the CRM. The aim is to cut manual CRM data entry; the time saved has not been measured.

**Demo limits:** to protect the API budget, the hosted demo allows at most 2,000 characters per note, 5 runs per visitor session, and a shared daily cap on total runs.

## 🏗️ Architecture & Tech Stack
* **LLM Engine:** Qwen 2.5 72B Instruct
* **API Gateway:** AICredits (OpenAI SDK compatible, enabling cost-effective and region-unlocked model access)
* **Frontend UI:** Streamlit (featuring token economy tracking, execution latency, and a developer payload view)
* **Deployment:** Docker (`python:3.11-slim`) with constrained memory limits via `.wslconfig` for efficient local execution.
* **Evaluation:** Custom Python evaluation loop for exact-match validation against a gold-standard dataset.

## 🧠 Japanese NLP & Prompt Engineering
Extracting data from Japanese business notes requires handling specific linguistic edge cases. The prompt architecture was iteratively engineered to enforce:
1. **Entity Standardization:** Automatically converting corporate shorthand (e.g., `(株)`, `(有)`) to formal legal entities (`株式会社`, `有限会社`) while preserving prefix/suffix positioning.
2. **Honorific Stripping:** Removing departmental noise and titles (`様`, `さん`, `社長`, `部長`) to isolate raw contact names.
3. **Nominal Phrase Formatting (体言止め):** Transforming conversational next-action verbs into professional, concise noun phrases.
4. **Temporal Normalization:** Stripping conversational suffixes (e.g., `まで`) from deadlines to ensure strict CRM date-string compliance.

## 📊 Evaluation Metrics
The pipeline is evaluated against a 30-note labeled dataset (`data/gold_30.jsonl`) with a strict exact-string match, plus an LLM-as-judge semantic score for the two free-text fields.

*Data note:* the 30 evaluation notes (`data/gold_30.jsonl`) are synthetic, LLM-generated Japanese business meeting notes with gold labels prepared for this eval; no real customer or interview data is used.

Measured at temperature=0 on 2026-09-30 (single run on GitHub Actions, same prompt and model as the app). Full details and per-note failure logs: [`eval/results.md`](eval/results.md).

### Results

Overall exact-match accuracy on 150 fields (30 notes × 5 fields), by iteration:

| Iteration | Exact match (150 fields) |
| :--- | :--- |
| Iteration 1 | 28.7% |
| Iteration 2 | 53.3% |
| Iteration 3, before temperature=0 ([details](eval/results_pre_t0.md)) | 56.0% (84/150) |
| Iteration 4, same prompt at temperature=0 (current) | **59.3%** (89/150) |

Per-field results (temperature=0):

| Field (抽出項目) | Exact match | Correct/Total | LLM-judge (semantic) | LLM-judge strict (match only) |
| :--- | :--- | :--- | :--- | :--- |
| **Contact (相手)** | 100.0% | 30/30 | — | — |
| **Company (会社名)** | 93.3% | 28/30 | — | — |
| **Deadline (期限)** | 80.0% | 24/30 | — | — |
| **Action (次アクション)** | 23.3% | 7/30 | 91.7% (25 match / 5 partial / 0 miss) | 83.3% (25/30) |
| **Risk (リスク)** | 0.0% | 0/30 | 75.0% (15 match / 15 partial / 0 miss) | 50.0% (15/30) |
| **Overall** | **59.3%** | **89/150** | | |

*Exact match* compares the strings after trimming whitespace. *LLM-judge (semantic)* covers only `次アクション` and `リスク`: the same model grades each prediction against the gold answer (`eval/judge.py`, prompt in `eval/judge_prompt.txt`, temperature 0) as match = 1, partial = 0.5, miss = 0. The strict column counts `match` only.

**How far to trust the judge:**
- The judge is the same model family as the extractor, so expect some self-judging bias.
- A manual spot-check of all 60 verdicts ([`eval/judge_spotcheck.md`](eval/judge_spotcheck.md)) agreed with 53/60 (88%). All 7 disagreements were the judge being too lenient.
- With the spot-check verdicts, the scores would be 81.7% (次アクション) and 73.3% (リスク).

**Compared with iteration 3:** the +3.3 points come from 次アクション (+3 notes) and 期限 (+3 notes); リスク dropped from 1/30 to 0/30. Both results are single runs on 30 notes, so part of the difference may be run-to-run variation rather than the temperature change.

**Cost and latency (measured in this run):**

| Run | API calls | Tokens (prompt + completion) | Est. cost | Avg latency |
| :--- | :--- | :--- | :--- | :--- |
| Extraction | 30 | 16,515 (14,382 + 2,133) | ≈ ₹0.64 (≈ ₹0.02 per note) | 4.6 s per note |
| LLM judge | 60 | 36,425 (34,532 + 1,893) | ≈ ₹1.40 | 2.6 s per call |

*The cost estimate uses the upstream rate of $0.36/M input and $0.40/M output tokens, plus the AICredits 5% forex buffer and 5% platform fee, at USD/INR 96.06. The exact amount charged is shown in the AICredits dashboard.*

### Failure analysis

Five representative misses from the temperature=0 run (gold → predicted):

1. **Correct paraphrase counted as wrong (exact-match limitation).** Note 1 リスク: `予算取りが難航している` → `予算取りの難航`. Same meaning in noun form; the judge says `match`. This is why リスク scores 0/30 on exact match: the gold labels mix sentence and noun styles, and no prediction matches them character-for-character.
2. **Second risk missing.** Note 5 リスク: `現状の運用フローへの不満、解約の可能性` → `解約の可能性`. The model often keeps only the most serious risk; 13 of the 15 `partial` リスク verdicts are cases like this.
3. **Deadline wording slip.** Note 25 期限: `今週水曜の午前中` → `今週水曜`. The time of day is lost. A smaller version of the same slip: `明日中` → `明日` (notes 10, 13, 30).
4. **Company-name rule broken.** Note 29 会社名: `ファーストステップ合同会社` → `合同会社ファーストステップ`. The prompt says to keep the legal-entity position, but the model moved it to the front. Also, in note 21 `(同)オメガパートナーズ` gives `オメガパートナーズ`, where the gold is `合同会社オメガパートナーズ`.
5. **Judge too lenient.** Note 13 次アクション: `修正要望の確認および回答` → `確認後、回答`. The judge says `match`, but the object (the revision requests) is missing, so the manual check scores it `partial`.

![Streamlit app: Japanese meeting note → CRM fields](docs/screenshot.png)

*The live deployed app (Streamlit Community Cloud) on a fictional sample note, showing latency/token telemetry, the demo-limit counter, and the raw JSON output.*

## 📂 Repository Structure
```text
├── .github/workflows/
│   ├── ci.yml                 # CI: pytest on Python 3.11 (no network, no secrets)
│   └── eval.yml               # Manual eval run (workflow_dispatch, uses the AICREDITS_API_KEY secret)
├── data/
│   └── gold_30.jsonl          # 30-note labeled evaluation dataset (frozen)
├── docs/
│   └── screenshot.png         # Live app screenshot (fictional sample note)
├── eval/
│   ├── run_eval.py            # Runs the extraction on the 30 notes, saves predictions + run metadata
│   ├── judge.py               # LLM-as-judge (semantic) scoring for 次アクション and リスク
│   ├── judge_prompt.txt       # Judge prompt (Japanese/English, JSON output)
│   ├── scoring.py             # Exact-match and judge-verdict scoring (pure functions)
│   ├── report.py              # Builds results.md from the saved files (no API calls)
│   ├── predictions_t0.jsonl   # Per-note predictions at temperature=0
│   ├── run_meta_t0.json       # Run date, calls, tokens, avg latency (extraction)
│   ├── judge_results.jsonl    # Per-field judge verdicts and reasons
│   ├── judge_meta.json        # Judge calls, tokens, latency and summary
│   ├── judge_spotcheck.md     # Manual check of all 60 judge verdicts
│   ├── results.md             # Current results, cost/latency, failure logs
│   └── results_pre_t0.md      # History: iteration 3 results before temperature=0
├── tests/                     # pytest unit tests (mocked client, no API key needed)
├── .dockerignore              # Docker build exclusions
├── .gitignore                 # Enforces security exclusions (.env, pycache)
├── Dockerfile                 # Container definition (Exposes port 8501)
├── README.md                  # Project documentation
├── README.ja.md               # Japanese README (日本語版)
├── app.py                     # Streamlit frontend with API telemetry and demo limits
├── demo_limits.py             # Input-length check and per-session / daily run caps
├── extractor.py               # The extraction API call + JSON parsing (used by app + eval)
├── prompts.py                 # Shared system prompt, model name and settings (used by app + eval)
├── pytest.ini                 # pytest settings
├── requirements.txt           # Minimal pinned runtime dependencies
└── requirements-dev.txt       # Test dependencies (pytest)
```

## 🚀 Quick Start (Local Deployment)

### Prerequisites

* Docker Desktop installed (with WSL2 configured for Windows users).
* An active AICredits API key.

### 1. Environment Setup

Clone the repository and create a `.env` file in the root directory to securely inject your API credentials:

```env
AICREDITS_API_KEY="your_actual_key_here"

```

### 2. Build the Docker Image

Construct the lightweight Python container:

```bash
docker build -t jp-crm-extractor .

```

### 3. Run the Application

Launch the container, mapping the Streamlit port and injecting the environment variables:

```bash
docker run --rm --name jp-crm-app -p 8501:8501 --env-file .env jp-crm-extractor

```

*(The `--rm` flag ensures the container automatically cleans itself up when stopped, preventing disk bloat).*

### 4. Access the UI

Navigate to `http://localhost:8501` in your web browser. Paste a Japanese meeting note into the input panel and execute the pipeline to view the structured CRM output, execution latency, and token economy metrics.

## 🧪 Tests and re-running the eval

Unit tests use a mocked API client, so they need no network and no API key:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

GitHub Actions runs the same tests on every push and pull request to `main` (Python 3.11).

To re-run the eval (about 90 API calls in total), set `AICREDITS_API_KEY` in your environment and run:

```bash
python eval/run_eval.py   # 30 extraction calls -> eval/predictions_t0.jsonl
python eval/judge.py      # 60 judge calls      -> eval/judge_results.jsonl
python eval/report.py     # no API calls        -> eval/results.md
```

The repo owner can also run this on GitHub Actions: **Actions → Eval (manual, uses API credits) → Run workflow**. The workflow reads the `AICREDITS_API_KEY` repository secret, stops if more than 100 calls are planned, and uploads the outputs as an artifact.

## ☁️ Deploy on Streamlit Community Cloud

1. At [share.streamlit.io](https://share.streamlit.io), click **Create app** and pick this repository, branch `main`, and main file path `app.py`.
2. Open **Advanced settings**, choose **Python 3.11** (the same version as the Docker image), and paste this into **Secrets**:

   ```toml
   AICREDITS_API_KEY = "your_actual_key_here"
   ```
3. Click **Deploy**. The app reads the key from the environment first and falls back to `st.secrets`. If the key is missing, the app shows setup instructions instead of the UI.

Community Cloud installs the pinned packages from `requirements.txt`. Apps with no traffic for 12 hours go to sleep; any visitor can wake one up from the sleep page.

## 🔭 Limitations & future work

- Done: semantic (LLM-as-judge) scoring for `次アクション` and `リスク`; measured cost and latency per note; unit tests and CI.
- The judge is the same model family as the extractor and was lenient in the spot-check. A different judge model, or a review by a Japanese-speaking domain expert, would make the semantic scores more reliable.
- Prompt fixes suggested by the failure analysis: keep `中` in deadlines (`明日中`, `午前中`), list every risk, keep the legal-entity position, and expand `(同)`. The prompt was intentionally left unchanged in this iteration.
- The eval set is small (30 synthetic notes), so a few notes change the score by several points.
- Let users edit the extracted fields in the UI, and show "not found" for missing fields.
