"""Fail-safe runner for paid eval batches (checkpoint + resume, budget caps, clean stop on billing errors).

Every finished call is appended to a JSONL checkpoint, keyed by run/path/note/field, so a re-run skips
completed keys. 402 / insufficient balance / quota errors stop at once (exit 3). A plain 429 rate limit
gets ONE backoff retry, then stops (exit 4). --max-calls is a hard cap; --per-day paces calls per IST day.
Before a batch it checks GET /api/credits (verified 2026-10-23; the documented /v1/credits returned 404) and stops while a buffer remains for the live demo.
The key is read from AICREDITS_API_KEY and never printed.
"""

import datetime
import json
import os
import time
import urllib.request

# Approved project limits (Oct 23, 2026). Override with flags; never raise without Prithivi's OK.
DEFAULT_MAX_CALLS = 2000
DEFAULT_PER_DAY = 400
DEFAULT_MAX_SPEND_INR = 100.0
DEFAULT_BUFFER_INR = 20.0  # left untouched for the live Streamlit demo (same account)
CREDITS_URL = "https://api.aicredits.in/api/credits"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

EXIT_OK, EXIT_CAP, EXIT_BALANCE, EXIT_BILLING, EXIT_RATE, EXIT_DAY = 0, 2, 5, 3, 4, 6
BILLING_WORDS = ("insufficient", "quota", "balance", "budget", "payment required", "credits")


class StopRun(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def make_key(run, path, note, field="*"):
    return f"{run}|{path}|{note}|{field}"


def load_done(checkpoint):
    done, calls_by_day, spend = set(), {}, 0.0
    if os.path.exists(checkpoint):
        with open(checkpoint, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    done.add(rec["key"])
                    calls_by_day[rec["day"]] = calls_by_day.get(rec["day"], 0) + rec.get("calls", 1)
                    spend += rec.get("cost_inr") or 0.0
    return done, calls_by_day, spend


def classify_error(exc):
    """Return 'billing', 'rate', or None. Works with openai errors (status_code/body) or plain exceptions."""
    status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    text = (str(getattr(exc, "body", "") or "") + " " + str(exc)).lower()
    if status == 402 or any(w in text for w in BILLING_WORDS):
        return "billing"
    if status == 429:
        return "rate"
    return None


def get_balance_inr(api_key, opener=urllib.request.urlopen, url=CREDITS_URL):
    """Free GET. Returns INR balance or None if the endpoint/shape is unknown."""
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with opener(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    d = data.get("data", data) if isinstance(data, dict) else {}
    for k in ("credits_inr", "balance_inr"):
        if isinstance(d.get(k), (int, float)):
            return float(d[k])
    return None


def run_batch(items, call, checkpoint, max_calls=DEFAULT_MAX_CALLS, per_day=DEFAULT_PER_DAY,
              max_spend_inr=DEFAULT_MAX_SPEND_INR, balance=None, buffer_inr=DEFAULT_BUFFER_INR,
              sleep=time.sleep, today=None, backoff_s=20):
    """items: list of (key, payload). call(payload) -> dict (may include cost_inr). Returns summary; raises StopRun."""
    if balance is not None:
        bal = balance()
        if bal is not None and bal <= buffer_inr:
            raise StopRun(EXIT_BALANCE, f"Balance ₹{bal:.2f} is at/below the ₹{buffer_inr:.2f} buffer kept for the live demo. Stopping.")
    done, by_day, spend = load_done(checkpoint)
    day = today or datetime.datetime.now(IST).date().isoformat()
    total = sum(by_day.values())
    made = skipped = 0
    for key, payload in items:
        if key in done:
            skipped += 1
            continue
        need = payload.get("max_calls", 1) if isinstance(payload, dict) else 1  # worst case for this item
        if total + need > max_calls:
            raise StopRun(EXIT_CAP, f"Hard cap of {max_calls} calls reached. Stopping.")
        if by_day.get(day, 0) + need > per_day:
            raise StopRun(EXIT_DAY, f"Daily pace of {per_day} calls reached for {day}. Resume tomorrow.")
        if spend >= max_spend_inr:
            raise StopRun(EXIT_CAP, f"Spend cap ₹{max_spend_inr:.2f} reached. Stopping.")
        attempts = 0
        while True:
            attempts += 1
            try:
                result = call(payload)
                break
            except Exception as e:
                kind = classify_error(e)
                try:  # keep the exact error (never the key) so a stop can be diagnosed
                    _msg = (str(getattr(e, "status_code", "")) + " " + type(e).__name__ + " " + str(getattr(e, "body", "") or e))[:600]
                    with open(os.path.join(os.path.dirname(checkpoint) or ".", "errors.log"), "a", encoding="utf-8") as ef:
                        ef.write(f"{key}\tkind={kind}\t{_msg}\n")
                except Exception:
                    pass
                if kind == "billing":
                    raise StopRun(EXIT_BILLING, "Billing/quota error from the API (402 or insufficient balance). Stopping, no retry.") from None
                if kind == "rate" and attempts == 1:
                    sleep(backoff_s)
                    continue
                if kind == "rate":
                    raise StopRun(EXIT_RATE, "Still rate-limited (429) after one backoff retry. Stopping.") from None
                result = {"success": False, "error": type(e).__name__}
                break
        used = result.pop("api_calls", None) or attempts  # exact count when the caller reports it
        rec = {"key": key, "day": day, "calls": used, "cost_inr": result.get("cost_inr"), "result": result}
        with open(checkpoint, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done.add(key)
        by_day[day] = by_day.get(day, 0) + used
        total += used
        spend += result.get("cost_inr") or 0.0
        made += 1
    return {"made": made, "skipped": skipped, "total_calls": total, "spend_inr": round(spend, 4)}
