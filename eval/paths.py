"""Where eval outputs live. Code stays in eval/; raw outputs go to eval/runs/<YYYY-MM-DD>/ (IST date)."""

import datetime
import os

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(EVAL_DIR, "runs")
BASELINE_RUN = os.path.join(RUNS_DIR, "2026-10-02")  # frozen accuracy eval (t0), missing_5, LLM judge
SECURITY_RUN = os.path.join(RUNS_DIR, "2026-10-12")  # attacks off/on, 3 defended repeats, held-out set
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def new_run_dir():
    """Output folder for a new run: $EVAL_RUN_DIR if set, else eval/runs/<today IST>."""
    d = os.getenv("EVAL_RUN_DIR") or os.path.join(RUNS_DIR, datetime.datetime.now(IST).strftime("%Y-%m-%d"))
    os.makedirs(d, exist_ok=True)
    return d


def read_dir(default):
    """Folder to read existing outputs from: $EVAL_RUN_DIR if set, else the given default."""
    return os.getenv("EVAL_RUN_DIR") or default
