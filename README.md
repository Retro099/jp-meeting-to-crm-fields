# JP Meeting Note to CRM Fields Extractor

日本語の商談メモからCRM項目（相手・会社名・期限・次アクション・リスク）をLLMで抽出し、正解データで精度を評価するプロジェクトです。

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
The pipeline was evaluated against a 30-note labeled dataset (`data/gold_30.jsonl`) using a strict exact-string match algorithm. Over three prompt iterations, the system achieved the following baseline:

*Data note:* the 30 evaluation notes (`data/gold_30.jsonl`) are synthetic, LLM-generated Japanese business meeting notes with gold labels prepared for this eval; no real customer or interview data is used.

*Temperature note:* these results were measured before `temperature=0` was set in the API calls (the model's default temperature was used). The numbers may shift slightly if the eval is re-run.

### Results

Overall exact-match accuracy on 150 fields (30 notes × 5 fields), by prompt iteration:

| Prompt iteration | Exact match (150 fields) |
| :--- | :--- |
| Iteration 1 | 28.7% |
| Iteration 2 | 53.3% |
| Iteration 3 (current) | **56.0%** (84/150) |

Per-field accuracy for iteration 3:

| Field (抽出項目) | Accuracy | Correct/Total | Notes |
| :--- | :--- | :--- | :--- |
| **Contact (相手)** | 100.0% | 30/30 | Perfectly stripped all titles and departments. |
| **Company (会社名)** | 93.3% | 28/30 | Handled implicit and explicit corporate entity formats. |
| **Deadline (期限)** | 70.0% | 21/30 | Misses are small wording differences (e.g. `明日` vs `明日中`); see `eval/results.md`. |
| **Action (次アクション)**| 13.3% | 4/30 | *Subject to exact-match metric limitations.* |
| **Risk (リスク)** | 3.3% | 1/30 | *Subject to exact-match metric limitations.* |
| **Overall Baseline** | **56.0%** | **84/150** | |

*Note on generative fields: exact match (Python `==`) is strict for free-text fields like `次アクション` and `リスク`. Many misses in `eval/results.md` are paraphrases of the expected answer, but some leave out part of it (e.g. a second risk). Semantic scoring (embedding similarity or LLM-as-a-judge) is planned but not done yet, so these numbers are exact-match only.*

![Streamlit app: Japanese meeting note → CRM fields](docs/screenshot.png)

*Streamlit app on a fictional sample note, showing latency/token telemetry and the raw JSON output.*

## 📂 Repository Structure
```text
├── data/
│   └── gold_30.jsonl          # 30-note labeled evaluation dataset
├── docs/
│   └── screenshot.png         # Streamlit app screenshot (fictional sample note)
├── eval/
│   ├── results.md             # Accuracy metrics and extraction failure logs
│   └── run_eval.py            # Automated evaluation execution script
├── .dockerignore              # Docker build exclusions
├── .gitignore                 # Enforces security exclusions (.env, pycache)
├── Dockerfile                 # Container definition (Exposes port 8501)
├── README.md                  # Project documentation
├── app.py                     # Streamlit frontend with API telemetry and demo limits
├── prompts.py                 # Shared system prompt, model name and settings (used by app + eval)
└── requirements.txt           # Minimal pinned runtime dependencies
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

## ☁️ Deploy on Streamlit Community Cloud

1. At [share.streamlit.io](https://share.streamlit.io), click **Create app** and pick this repository, branch `main`, and main file path `app.py`.
2. Open **Advanced settings**, choose **Python 3.11** (the same version as the Docker image), and paste this into **Secrets**:

   ```toml
   AICREDITS_API_KEY = "your_actual_key_here"
   ```
3. Click **Deploy**. The app reads the key from the environment first and falls back to `st.secrets`. If the key is missing, the app shows setup instructions instead of the UI.

Community Cloud installs the pinned packages from `requirements.txt`. Apps with no traffic for 12 hours go to sleep; any visitor can wake one up from the sleep page.
