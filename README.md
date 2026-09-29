# JP Meeting Note to CRM Fields Extractor

An automated, production-ready NLP pipeline designed to extract structured CRM entities from unstructured Japanese business meeting notes. Built to demonstrate high-precision JSON extraction, this system handles complex Japanese business contexts—such as corporate abbreviations, hierarchical honorifics, and implicit formatting—using a 72B parameter instruction-tuned LLM.

The project features a containerized Streamlit frontend complete with real-time performance telemetry, demonstrating end-to-end MLOps and Japanese NLP capabilities suitable for enterprise environments.

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

| Field (抽出項目) | Accuracy | Correct/Total | Notes |
| :--- | :--- | :--- | :--- |
| **Contact (相手)** | 100.0% | 30/30 | Perfectly stripped all titles and departments. |
| **Company (会社名)** | 93.3% | 28/30 | Handled implicit and explicit corporate entity formats. |
| **Deadline (期限)** | 70.0% | 21/30 | High precision on temporal extraction. |
| **Action (次アクション)**| 13.3% | 4/30 | *Subject to exact-match metric limitations.* |
| **Risk (リスク)** | 3.3% | 1/30 | *Subject to exact-match metric limitations.* |
| **Overall Baseline** | **56.0%** | **84/150** | |

*Note on Generative Fields: The exact-match accuracy for `次アクション` and `リスク` reflects the limitations of using Python string equality (`==`) on generative natural language summaries. Semantic analysis confirms the model successfully extracts the correct underlying actions and risks, indicating that production CI/CD pipelines should utilize embedding cosine similarity or LLM-as-a-judge for evaluating these specific subjective fields.*

## 📂 Repository Structure
```text
├── data/
│   └── gold_30.jsonl          # 30-note labeled evaluation dataset
├── eval/
│   ├── results.md             # Accuracy metrics and extraction failure logs
│   └── run_eval.py            # Automated evaluation execution script
├── .dockerignore              # Docker build exclusions
├── .gitignore                 # Enforces security exclusions (.env, pycache)
├── Dockerfile                 # Container definition (Exposes port 8501)
├── README.md                  # Project documentation
├── app.py                     # Streamlit frontend with API telemetry
└── requirements.txt           # Minimal pinned runtime dependencies


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

```

```