import datetime
import json
import os
import threading

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from crm_extractor import security
from crm_extractor.demo_limits import DAILY_CAP, MAX_CHARS, MAX_RUNS_PER_SESSION, reserve_run, validate_note
from crm_extractor.extractor import extract_crm_data
from crm_extractor.prompts import API_BASE_URL, CRM_FIELDS, NOT_FOUND
from crm_extractor.ui_strings import DEFAULT_LANG, LANG_LABELS, t

load_dotenv()

# Demo limits (MAX_CHARS, MAX_RUNS_PER_SESSION, DAILY_CAP) live in crm_extractor/demo_limits.py
# UI text (Japanese default, English) lives in crm_extractor/ui_strings.py

# --- UI Layout & Styling ---
st.set_page_config(page_title="CRM Data Extractor", page_icon="🏢", layout="wide")

# Language toggle (Japanese is the default)
with st.sidebar:
    lang = st.radio(
        t(DEFAULT_LANG, "language"),
        options=list(LANG_LABELS),
        format_func=LANG_LABELS.get,
        horizontal=True,
        key="lang",
    )


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
    st.error(t(lang, "missing_key"))
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
            st.session_state.runs_used, usage["counts"], _today(), MAX_RUNS_PER_SESSION, DAILY_CAP, lang=lang)
        if not allowed:
            return message
        usage["counts"] = new_counts
    st.session_state.runs_used += 1
    return None


if "runs_used" not in st.session_state:
    st.session_state.runs_used = 0
if "result" not in st.session_state:
    st.session_state.result = None  # last successful extraction, kept so edits survive reruns


def _edit_key(field):
    return f"edit_{field}"


def edited_values():
    """The five fields as currently edited in the UI (prefilled from the model output)."""
    return {f: st.session_state.get(_edit_key(f), NOT_FOUND) for f in CRM_FIELDS}


# Sidebar: System Telemetry
with st.sidebar:
    st.header(t(lang, "sidebar_header"))
    st.info(t(lang, "sidebar_engine"))
    st.info(t(lang, "sidebar_gateway"))
    st.info(t(lang, "sidebar_task"))
    st.markdown("---")
    defenses_on = st.toggle(t(lang, "defenses_toggle"), value=security.defenses_enabled(),
                            help=t(lang, "defenses_help"), key="defenses")
    (st.success if defenses_on else st.caption)(t(lang, "defenses_on" if defenses_on else "defenses_off"))
    st.markdown("---")
    st.caption(t(lang, "sidebar_caption"))

def render_note_scan(hits, defended):
    """Instruction-like lines found in the input note (shown even when the output is clean)."""
    if not hits:
        return False
    if defended:
        st.warning(t(lang, "note_scan_defended"))
    else:
        st.error(t(lang, "note_scan_undefended"))
    for h in hits:
        st.code(h, language=None)
    return True


def render_security_panel(report, note_hits=(), defended=True):
    """Plain list of what the defenses blocked or flagged, and why."""
    st.markdown(t(lang, "security_header"))
    found = render_note_scan(note_hits, defended)
    if not defended:
        return
    events = security.security_events(report)
    if not events and found:
        return
    if not events:
        st.caption("✅ " + t(lang, "security_clean"))
        return
    for level, field, reason in events:
        label = t(lang, f"field_{field}") if field in CRM_FIELDS else (field or t(lang, "field_general"))
        line = f"**{t(lang, 'level_' + level)}** · {label}: {t(lang, 'reason_' + reason)}"
        (st.error if level == "block" else st.warning)(line)


st.title(t(lang, "title"))

col1, col2 = st.columns([1, 1.2]) # Slightly wider right column for better data display

with col1:
    st.subheader(t(lang, "input_header"))
    note_input = st.text_area(
        t(lang, "input_label"),
        height=250,
        placeholder="【商談メモ】 10/28 (株)グローバルテック 営業部 佐藤部長、田中さん。...",
        max_chars=MAX_CHARS,
        help=t(lang, "input_help", max_chars=MAX_CHARS),
        key="note_input",
    )
    st.caption(t(lang, "privacy_note"))
    usage_caption = st.empty()  # filled in at the end, after this run is counted
    extract_btn = st.button(t(lang, "run_button"), type="primary", use_container_width=True)

with col2:
    st.subheader(t(lang, "results_header"))

    if extract_btn:
        note_problem = validate_note(note_input, MAX_CHARS, lang=lang)
        if note_problem is not None:
            level, message = note_problem
            (st.warning if level == "warning" else st.error)(message)
        elif (limit_error := try_reserve_run()) is not None:
            st.warning(limit_error)
        else:
            st.session_state.result = None
            note_hits = security.scan_note_for_injection(note_input)  # no LLM call
            with st.spinner(t(lang, "spinner")):
                result = extract_crm_data(client, note_input, defenses=defenses_on)
            if not result["success"] and (result.get("security") or {}).get("canary_leak"):
                st.error(t(lang, "canary_blocked"))
                render_note_scan(note_hits, defenses_on)
            elif not result["success"]:
                st.error(t(lang, "extraction_failed", error=result["error"]))
            else:
                result["note_hits"] = note_hits
                result["defended"] = defenses_on
                st.session_state.result = result
                for f in CRM_FIELDS:  # prefill the editable fields (未検出 is shown as-is)
                    st.session_state[_edit_key(f)] = result["data"][f]

    result = st.session_state.result
    if result is not None:
        st.success(t(lang, "extraction_done", latency=result["latency"]))

        # Performance Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t(lang, "metric_latency"), f"{result['latency']}s")
        m2.metric(t(lang, "metric_prompt_tokens"), result["prompt_tokens"])
        m3.metric(t(lang, "metric_completion_tokens"), result["completion_tokens"])
        m4.metric(t(lang, "metric_total_tokens"), result["total_tokens"])

        if "security" in result or result.get("note_hits"):
            render_security_panel(result.get("security"), result.get("note_hits", []),
                                  defended=result.get("defended", "security" in result))

        st.divider()

        # Editable CRM fields, prefilled with the model output
        st.markdown(t(lang, "output_header"))
        st.caption(t(lang, "edit_help", not_found=NOT_FOUND))
        for f in CRM_FIELDS:
            if f == "リスク":
                st.text_area(t(lang, f"field_{f}"), key=_edit_key(f), height=90)
            else:
                st.text_input(t(lang, f"field_{f}"), key=_edit_key(f))

        edited_json = json.dumps(edited_values(), ensure_ascii=False, indent=2)
        st.caption(t(lang, "edited_json_label"))
        st.code(edited_json, language="json")
        st.download_button(
            t(lang, "download_button"),
            data=edited_json.encode("utf-8"),
            file_name="crm_fields.json",
            mime="application/json",
            use_container_width=True,
        )

        st.divider()

        # Developer View for the raw JSON payload (before normalization and edits)
        with st.expander(t(lang, "raw_json_expander")):
            st.json(result.get("raw_data", result["data"]))

usage_caption.caption(t(lang, "usage_caption", chars=len(note_input or ""), max_chars=MAX_CHARS,
                        left=MAX_RUNS_PER_SESSION - st.session_state.runs_used, max_runs=MAX_RUNS_PER_SESSION))
