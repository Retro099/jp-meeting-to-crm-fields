"""Eval v2: old single-call path vs the optional LangGraph agent, in one session, on the same data.

Phases (cheapest high-value first, so a cap hit still leaves complete sections):
  1. extract  - data/gold_30.jsonl x {old, agent} x 3 runs, defenses off (same setting as the frozen eval)
  2. attacks  - data/attacks_v2_heldout.jsonl x {old, agent} x {off, on} x 3 runs (fixed canary)
  3. judge    - one judge call per field (5) for every successful extraction in phase 1

Every call goes through eval/safe_runner.py: JSONL checkpoint + resume, 402/quota stop, one 429 retry,
hard caps (2,000 calls, 400/day IST, INR 100) and a balance stop at INR 20 via GET /api/credits.
Temperature 0 everywhere; repeated runs still measure any provider-side non-determinism.

Usage (key only via env AICREDITS_API_KEY, never printed):
    python eval/eval_v2.py --out /workspace/crm-eval-v2            # one pass until done/stop
    python eval/eval_v2.py --out /workspace/crm-eval-v2 --driver   # loop: sleep to 00:05 IST on the daily cap
"""

import argparse
import datetime
import json
import os
import sys
import time
from types import SimpleNamespace

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(EVAL_DIR, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, EVAL_DIR)
import safe_runner as sr  # noqa: E402
from attack_scoring import attack_succeeded  # noqa: E402
from scoring import FIELDS, exact_match  # noqa: E402

from crm_extractor.agent import MAX_REPAIRS, extract_crm_data_agent  # noqa: E402
from crm_extractor.extractor import extract_crm_data  # noqa: E402
from crm_extractor.prompts import API_BASE_URL, MODEL_NAME  # noqa: E402

RUNS = 3
PATHS = ("old", "agent")
CANARY = "CANARY-7f3a9c2e51d84b60"  # same test-only marker as run_attacks.py
GOLD = os.path.join(ROOT, "data", "gold_30.jsonl")
ATTACKS = os.path.join(ROOT, "data", "attacks_v2_heldout.jsonl")
JUDGE_PROMPT = os.path.join(EVAL_DIR, "judge_v2_prompt.txt")
# Price per token in INR for qwen/qwen-2.5-72b-instruct, from the public GET /api/models (2026-10-23).
PRICE_IN_INR = 3.5872703118e-05
PRICE_OUT_INR = 3.985855902e-05
CHUNK = 25  # balance is re-checked before every chunk
IST = sr.IST


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class ApiError(Exception):
    def __init__(self, text):
        super().__init__(text)
        low = text.lower()
        self.status_code = 402 if "error code: 402" in low else 429 if "error code: 429" in low else None
        self.body = text


class Meter:
    """Wraps the OpenAI client; counts every request (incl. failed) and its token cost."""

    def __init__(self, client):
        self._client = client
        self.calls = self.pending_calls = 0
        self.pending_cost = 0.0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.calls += 1
        self.pending_calls += 1
        resp = self._client.chat.completions.create(**kw)
        u = getattr(resp, "usage", None)
        self.pending_cost += (getattr(u, "prompt_tokens", 0) or 0) * PRICE_IN_INR + (getattr(u, "completion_tokens", 0) or 0) * PRICE_OUT_INR
        return resp

    def take(self):
        c, cost = self.pending_calls, self.pending_cost
        self.pending_calls, self.pending_cost = 0, 0.0
        return c, round(cost, 6)


def run_path(client, path, text, defenses, canary=None):
    fn = extract_crm_data_agent if path == "agent" else extract_crm_data
    r = fn(client, text, defenses=defenses, canary=canary)
    if not r["success"] and isinstance(r.get("error"), str) and sr.classify_error(ApiError(r["error"])):
        raise ApiError(r["error"])  # billing / rate-limit errors must reach the runner, not be scored
    return r


def judge_prompt(template, field, note, gold, pred):
    return (template.replace("<<FIELD>>", field).replace("<<NOTE>>", note)
            .replace("<<GOLD>>", str(gold)).replace("<<PRED>>", str(pred) if str(pred).strip() else "(空 / empty)"))


def parse_judge(text):
    d = json.loads(text)
    v = str(d.get("verdict", "")).strip().lower()
    if v not in ("match", "partial", "miss"):
        raise ValueError(f"unknown verdict {v!r}")
    return {"verdict": v, "supported": bool(d.get("supported")), "reason": str(d.get("reason", ""))[:300]}


def make_caller(client, meter, sleep=time.sleep, pause=1.0):
    template = open(JUDGE_PROMPT, encoding="utf-8").read()

    def call(p):
        kind = p["kind"]
        if kind == "extract":
            r = run_path(client, p["path"], p["input"], defenses=False)
            pred = r.get("data", {}) if r["success"] else {}
            out = {"success": r["success"], "error": r.get("error"), "predicted": pred,
                   "exact": {f: exact_match(p["expected"].get(f, ""), pred.get(f, "")) for f in FIELDS} if r["success"] else None,
                   "latency": r.get("latency"), "prompt_tokens": r.get("prompt_tokens"),
                   "completion_tokens": r.get("completion_tokens"), "agent": r.get("agent")}
        elif kind == "attack":
            r = run_path(client, p["path"], p["input"], defenses=p["defenses"], canary=CANARY)
            out = {"success": r["success"], "error": r.get("error"),
                   "attack_success": attack_succeeded(p["case"], r, CANARY), "category": p["case"]["category"],
                   "latency": r.get("latency"), "agent": r.get("agent")}
        else:
            resp = client.chat.completions.create(model=MODEL_NAME, temperature=0, response_format={"type": "json_object"},
                                                  messages=[{"role": "user", "content": judge_prompt(template, p["field"], p["input"], p["gold"], p["pred"])}])
            try:
                out = {"success": True, **parse_judge(resp.choices[0].message.content)}
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                out = {"success": False, "error": f"judge parse: {e}"}
            out.update({"field": p["field"], "gold": p["gold"], "pred": p["pred"]})
        calls, cost = meter.take()
        out["api_calls"], out["cost_inr"] = calls, cost
        sleep(pause)
        return out

    return call


def extract_items(gold):
    items = []
    for run in range(1, RUNS + 1):
        for path in PATHS:
            for i, g in enumerate(gold, 1):
                items.append((sr.make_key(f"extract-r{run}", path, f"n{i:02d}"),
                              {"kind": "extract", "path": path, "input": g["input"], "expected": g["expected"],
                               "max_calls": 1 + MAX_REPAIRS if path == "agent" else 1}))
    return items


def attack_items(cases):
    items = []
    for run in range(1, RUNS + 1):
        for mode in ("off", "on"):
            for path in PATHS:
                for c in cases:
                    items.append((sr.make_key(f"attack-{mode}-r{run}", path, c["id"]),
                                  {"kind": "attack", "path": path, "defenses": mode == "on", "input": c["input"], "case": c,
                                   "max_calls": 1 + MAX_REPAIRS if path == "agent" else 1}))
    return items


def judge_items(checkpoint, gold):
    done = {}
    if os.path.exists(checkpoint):
        for rec in load_jsonl(checkpoint):
            if rec["key"].startswith("extract-"):
                done[rec["key"]] = rec["result"]
    items = []
    for run in range(1, RUNS + 1):
        for path in PATHS:
            for i, g in enumerate(gold, 1):
                r = done.get(sr.make_key(f"extract-r{run}", path, f"n{i:02d}"))
                if not r or not r.get("success"):
                    continue  # failed extraction is scored as miss without a judge call
                for f in FIELDS:
                    items.append((sr.make_key(f"judge-r{run}", path, f"n{i:02d}", f),
                                  {"kind": "judge", "field": f, "input": g["input"], "gold": g["expected"].get(f, ""),
                                   "pred": r["predicted"].get(f, "")}))
    return items


def phases(checkpoint):
    gold = load_jsonl(GOLD)
    yield "extract", extract_items(gold)
    yield "attacks", attack_items(load_jsonl(ATTACKS))
    yield "judge", judge_items(checkpoint, gold)  # built after phase 1 is complete


def run_all(call, checkpoint, balance, sleep=time.sleep, **caps):
    out = {}
    for name, items in phases(checkpoint):
        for start in range(0, len(items), CHUNK):
            out[name] = sr.run_batch(items[start:start + CHUNK], call, checkpoint, balance=balance, sleep=sleep, **caps)
    return out


def spend_by_phase(checkpoint):
    agg = {}
    if os.path.exists(checkpoint):
        for rec in load_jsonl(checkpoint):
            ph = rec["key"].split("-")[0]
            a = agg.setdefault(ph, {"calls": 0, "inr": 0.0})
            a["calls"] += rec.get("calls", 0)
            a["inr"] = round(a["inr"] + (rec.get("cost_inr") or 0), 4)
    return agg


def write_status(out_dir, state, reason, meter_pending=(0, 0.0), balance=None):
    by = spend_by_phase(os.path.join(out_dir, "checkpoint.jsonl"))
    status = {"state": state, "reason": reason,
              "updated_ist": datetime.datetime.now(IST).isoformat(timespec="seconds"),
              "calls": sum(v["calls"] for v in by.values()) + meter_pending[0],
              "inr_spent_est": round(sum(v["inr"] for v in by.values()) + meter_pending[1], 4),
              "unrecorded_calls_at_stop": meter_pending[0], "per_step": by, "last_balance_inr": balance,
              "spend_note": "INR is estimated from tokens x the /api/models price; compare with the dashboard."}
    with open(os.path.join(out_dir, "STATUS.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    return status


def seconds_to_next_0005(now=None):
    now = now or datetime.datetime.now(IST)
    nxt = (now + datetime.timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return max(60, (nxt - now).total_seconds())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/workspace/crm-eval-v2")
    ap.add_argument("--driver", action="store_true", help="keep going across days until done or a hard stop")
    ap.add_argument("--max-calls", type=int, default=sr.DEFAULT_MAX_CALLS)
    ap.add_argument("--per-day", type=int, default=sr.DEFAULT_PER_DAY)
    ap.add_argument("--max-spend-inr", type=float, default=sr.DEFAULT_MAX_SPEND_INR)
    ap.add_argument("--buffer-inr", type=float, default=sr.DEFAULT_BUFFER_INR)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    key = os.environ.get("AICREDITS_API_KEY")
    if not key:
        sys.exit("AICREDITS_API_KEY is not set.")
    from openai import OpenAI
    meter = Meter(OpenAI(api_key=key, base_url=API_BASE_URL, timeout=90, max_retries=0))
    last = {"bal": None}

    def balance():
        last["bal"] = sr.get_balance_inr(key)
        print(f"[{datetime.datetime.now(IST):%H:%M:%S} IST] balance check: INR {last['bal']}", flush=True)
        return last["bal"]

    call = make_caller(meter, meter)
    cp = os.path.join(a.out, "checkpoint.jsonl")
    caps = {"max_calls": a.max_calls, "per_day": a.per_day, "max_spend_inr": a.max_spend_inr, "buffer_inr": a.buffer_inr}
    while True:
        try:
            run_all(call, cp, balance, **caps)
            st = write_status(a.out, "done", "all phases complete", meter.take(), last["bal"])
            print(json.dumps(st), flush=True)
            return 0
        except sr.StopRun as e:
            if e.code == sr.EXIT_DAY and a.driver:
                wait = seconds_to_next_0005()
                print(f"{e} Sleeping {wait / 3600:.1f} h until 00:05 IST.", flush=True)
                time.sleep(wait)
                continue
            st = write_status(a.out, "stopped", str(e), meter.take(), last["bal"])
            print(json.dumps(st), flush=True)
            return e.code


if __name__ == "__main__":
    sys.exit(main())
