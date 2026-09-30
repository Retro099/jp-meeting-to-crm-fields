import datetime
import os
import threading

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from demo_limits import DAILY_CAP, MAX_CHARS, MAX_RUNS_PER_SESSION, reserve_run, validate_note
from extractor import extract_crm_data
from prompts import API_BASE_URL

load_dotenv()

# Demo limits (MAX_CHARS, MAX_RUNS_PER_SESSION, DAILY_CAP) live in demo_limits.py

# --- UI Layout & Styling ---
st.set_page_config(page_title="CRM Data Extractor", page_icon="🏢", layout="wide")


def get_api_key():
    """Read the key from the environment (.env / Docker), then from Streamlit secrets."""
    key = os.getenv("AICREDITS_API_KEY")
    if key:
        return key
    try:
        return st.secrets["AICREDITS_API_KEY"]
    except Exception:
        return None


api_key = get_api_key()
if not api_key:
    st.error(
        "**AICREDITS_API_KEY is not set.**\n\n"
        "- Local: add `AICREDITS_API_KEY=\"your_key\"` to a `.env` file in the repo root.\n"
        "- Docker: run with `--env-file .env`.\n"
        "- Streamlit Community Cloud: add `AICREDITS_API_KEY = \"your_key\"` under App settings → Secrets."
    )
    st.stop()

client = OpenAI(api_key=api_key, base_url=API_BASE_URL)


@st.cache_resource
def _daily_usage():
    """Run counts per UTC date, shared across all sessions of this app process."""
    return {"lock": threading.Lock(), "counts": {}}


def _today():
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def daily_runs_used():
    return _daily_usage()["counts"].get(_today(), 0)


def try_reserve_run():
    """Count one run against the session and daily caps. Returns an error message, or None if allowed."""
    usage = _daily_usage()
    with usage["lock"]:
        allowed, message, new_counts = reserve_run(
            st.session_state.runs_used, usage["counts"], _today(), MAX_RUNS_PER_SESSION, DAILY_CAP)
        if not allowed:
            return message
        usage["counts"] = new_counts
    st.session_state.runs_used += 1
    return None


if "runs_used" not in st.session_state:
    st.session_state.runs_used = 0


# Sidebar: System Telemetry
with st.sidebar:
    st.header("⚙️ System Telemetry")
    st.info("**Engine:** Qwen 2.5 72B Instruct")
    st.info("**Gateway:** AICredits (OpenAI API)")
    st.info("**Task:** CRM Entity Extraction")
    st.markdown("---")
    st.caption("Designed for Japanese Business Contexts.")

st.title("📝 Japanese Meeting Note to CRM Fields")

col1, col2 = st.columns([1, 1.2]) # Slightly wider right column for better data display

with col1:
    st.subheader("1. Input Data")
    note_input = st.text_area(
        "Paste Japanese meeting note here:", 
        height=250, 
        placeholder="【商談メモ】 10/28 (株)グローバルテック 営業部 佐藤部長、田中さん。...",
        max_chars=MAX_CHARS,
    )
    usage_caption = st.empty()  # filled in at the end, after this run is counted
    extract_btn = st.button("Run Extraction Pipeline", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Extraction Results")
    
    if extract_btn:
        note_problem = validate_note(note_input, MAX_CHARS)
        if note_problem is not None:
            level, message = note_problem
            (st.warning if level == "warning" else st.error)(message)
        elif (limit_error := try_reserve_run()) is not None:
            st.warning(limit_error)
        else:
            with st.spinner("Processing via Qwen 72B..."):
                result = extract_crm_data(client, note_input)
                
                if not result["success"]:
                    st.error(f"Extraction failed: {result['error']}")
                else:
                    st.success(f"Extraction complete in {result['latency']} seconds ⚡")
                    
                    # Performance Metrics Row
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Latency", f"{result['latency']}s")
                    m2.metric("Prompt Tokens", result["prompt_tokens"])
                    m3.metric("Completion Tokens", result["completion_tokens"])
                    m4.metric("Total Tokens", result["total_tokens"])
                    
                    st.divider()
                    
                    # Clean Business Presentation
                    st.markdown("### 📋 CRM Output")
                    data = result["data"]
                    
                    # Using Markdown for a clean, readable layout instead of raw JSON
                    st.markdown(f"**🏢 会社名 (Company):** `{data.get('会社名', 'N/A')}`")
                    st.markdown(f"**👤 相手 (Contact):** `{data.get('相手', 'N/A')}`")
                    st.markdown(f"**📅 期限 (Deadline):** `{data.get('期限', 'N/A')}`")
                    st.markdown(f"**🎯 次アクション (Next Action):** `{data.get('次アクション', 'N/A')}`")
                    
                    # Risk gets a highlight box
                    st.info(f"**⚠️ リスク (Risk):** {data.get('リスク', 'N/A')}")
                    
                    st.divider()
                    
                    # Developer View for the raw JSON payload
                    with st.expander("🛠️ Developer View (Raw JSON Payload)"):
                        st.json(data)

usage_caption.caption(
    f"{len(note_input)}/{MAX_CHARS} characters · "
    f"{MAX_RUNS_PER_SESSION - st.session_state.runs_used}/{MAX_RUNS_PER_SESSION} demo runs left this session"
)
