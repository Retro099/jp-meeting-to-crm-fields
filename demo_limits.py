"""Demo limits for the public Streamlit app (pure functions, no Streamlit import)."""

from ui_strings import t

MAX_CHARS = 2000            # max characters per note
MAX_RUNS_PER_SESSION = 5    # max extractions per visitor session
DAILY_CAP = 50              # max extractions per day, shared by all visitors (UTC date)


def validate_note(text, max_chars=MAX_CHARS, lang="en"):
    """Return None if the note can be sent, else (level, message) with level "warning" or "error"."""
    if not text or not text.strip():
        return ("warning", t(lang, "empty_note"))
    if len(text) > max_chars:
        return ("error", t(lang, "note_too_long", length=len(text), max_chars=max_chars))
    return None


def reserve_run(session_runs_used, daily_counts, today,
                max_runs_per_session=MAX_RUNS_PER_SESSION, daily_cap=DAILY_CAP, lang="en"):
    """Decide whether one more run is allowed.

    Returns (allowed, message, new_daily_counts). new_daily_counts only keeps today's count.
    """
    if session_runs_used >= max_runs_per_session:
        return (False, t(lang, "session_limit", max_runs=max_runs_per_session), daily_counts)
    used_today = daily_counts.get(today, 0)
    if used_today >= daily_cap:
        return (False, t(lang, "daily_limit"), daily_counts)
    return (True, None, {today: used_today + 1})
