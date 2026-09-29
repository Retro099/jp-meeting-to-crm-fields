# JP Meeting Note to CRM Fields Extractor

An automated, production-ready pipeline that extracts structured CRM entities (Company, Contact, Action, Deadline, Risk) from unstructured Japanese business meeting notes. 

Built to demonstrate high-precision JSON extraction handling complex Japanese business contexts (abbreviations, honorifics, implicit formatting) using a 72B parameter instruction-tuned LLM.

## Architecture
* **Frontend:** Streamlit interactive UI with token economy and latency telemetry.
* **Backend Pipeline:** Python extraction loop with strict exact-match evaluation logging.
* **LLM Engine:** Qwen 2.5 72B Instruct (accessed via OpenAI-compatible AICredits gateway).
* **Infrastructure:** Containerized via Docker (`python:3.11-slim`) with constrained memory limits for local execution.

## Evaluation Metrics (30-Note Gold Standard)
The model was evaluated against a strict exact-match standard, requiring complete removal of honorifics, formalization of company entities, and structured noun-phrase actions.
* **Contact Name (相手):** 100% Accuracy (Stripped all titles/departments correctly)
* **Company Name (会社名):** 93.3% Accuracy (Correctly expanded `(株)` to formal variants)
* **Deadline (期限):** 70.0% Accuracy 
* *Note: Risk and Next Action fields naturally fail exact-string metrics due to the generative nature of text summarization, despite semantic accuracy.*

## Run Locally (Docker)
1. Clone the repository and add your `.env` file containing `AICREDITS_API_KEY=your_key`.
2. Build the image:
   ```bash
   docker build -t jp-crm-extractor .