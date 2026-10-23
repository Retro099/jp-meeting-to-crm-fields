"""Optional LangGraph agent: extract -> validate -> repair (max 2 retries) -> done.

EXPERIMENTAL and opt-in. The default path is still `extractor.extract_crm_data` (unchanged).
Reuses the shared prompt (prompts.py), the message builders and parsing in extractor.py, and
the schema check in security.py. The OpenAI-compatible client is passed in, so tests run with a fake.
"""

import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from . import security
from .extractor import build_defended_messages, build_messages, normalize_fields, parse_json_object
from .prompts import CRM_FIELDS, MODEL_NAME, TEMPERATURE

MAX_REPAIRS = 2


class AgentState(TypedDict, total=False):
    messages: list
    content: str
    raw: dict
    errors: list
    attempts: int
    calls: int
    usage: dict


def validate_output(content):
    """Return (raw_dict_or_None, errors). Errors are plain strings fed back to the model on repair."""
    try:
        raw = parse_json_object(content)
    except ValueError as e:
        return None, [str(e)]
    errors = [f"missing key: {f}" for f in CRM_FIELDS if f not in raw]
    _, problems = security.validate_schema({k: v for k, v in raw.items() if k in CRM_FIELDS})
    return raw, errors + problems


def repair_message(errors):
    lines = "\n".join(f"- {e}" for e in errors)
    return {"role": "user", "content": "前回の出力はスキーマ検証に失敗しました。以下の問題を修正し、5つのキーを持つ厳密なJSONのみを再出力してください。\n" + lines}


def build_graph(client):
    def call(state):
        start = time.perf_counter()
        resp = client.chat.completions.create(model=MODEL_NAME, messages=state["messages"],
                                              response_format={"type": "json_object"}, temperature=TEMPERATURE)
        usage = dict(state.get("usage") or {})
        u = getattr(resp, "usage", None)
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            v = getattr(u, k, None)
            if isinstance(v, int):
                usage[k] = usage.get(k, 0) + v
        usage["latency"] = round(usage.get("latency", 0) + time.perf_counter() - start, 2)
        content = resp.choices[0].message.content
        return {"content": content, "calls": state.get("calls", 0) + 1, "usage": usage,
                "messages": state["messages"] + [{"role": "assistant", "content": content or ""}]}

    def validate(state):
        raw, errors = validate_output(state["content"])
        return {"raw": raw, "errors": errors}

    def repair(state):
        return {"messages": state["messages"] + [repair_message(state["errors"])], "attempts": state.get("attempts", 0) + 1}

    def route(state):
        if not state["errors"]:
            return "done"
        return "repair" if state.get("attempts", 0) < MAX_REPAIRS else "done"

    g = StateGraph(AgentState)
    g.add_node("extract", call)
    g.add_node("validate", validate)
    g.add_node("repair", repair)
    g.add_edge(START, "extract")
    g.add_edge("extract", "validate")
    g.add_conditional_edges("validate", route, {"repair": "repair", "done": END})
    g.add_edge("repair", "extract")
    return g.compile()


def extract_crm_data_agent(client, text, defenses=None, canary=None):
    """Same return shape as extract_crm_data, plus `agent` = {calls, repairs, errors}."""
    if defenses is None:
        defenses = security.defenses_enabled()
    if defenses:
        canary = canary or security.new_canary()
        messages = build_defended_messages(text, security.new_boundary(), canary)
    else:
        messages = build_messages(text, canary)
    try:
        s = build_graph(client).invoke({"messages": messages, "attempts": 0, "calls": 0})
    except Exception as e:
        return {"success": False, "error": str(e)}
    usage = s.get("usage", {})
    agent = {"calls": s["calls"], "repairs": s.get("attempts", 0), "errors": s["errors"], "valid": not s["errors"]}
    base = {"latency": usage.get("latency"), "agent": agent,
            **{k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens")}}
    if defenses and security.scan_for_canary(s["content"], canary):
        return {"success": False, "error": "blocked: output contained the secret canary (possible prompt leak)",
                "security": {"blocked": True, "canary_leak": True}, **base}
    if s["raw"] is None:
        return {"success": False, "error": "; ".join(s["errors"]), **base}
    raw = s["raw"]
    extra = {}
    if defenses:
        data, report = security.harden_output(s["content"], raw, canary, note=text)
        raw = dict(data)
        extra["security"] = report
    else:
        data = normalize_fields(raw)
    return {"success": True, "data": data, "raw_data": raw, **extra, **base}
