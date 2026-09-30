"""Demo limits for the public Streamlit app (pure functions, no Streamlit import)."""

MAX_CHARS = 2000            # max characters per note
MAX_RUNS_PER_SESSION = 5    # max extractions per visitor session
DAILY_CAP = 50              # max extractions per day, shared by all visitors (UTC date)


def validate_note(text, max_chars=MAX_CHARS):
    """Return None if the note can be sent, else (level, message) with level "warning" or "error"."""
    if not text or not text.strip():
        return ("warning", "Please enter a meeting note first.")
    if len(text) > max_chars:
        return ("error", f"The note is too long ({len(text)} characters). The limit is {max_chars} characters.")
    return None


def reserve_run(session_runs_used, daily_counts, today,
                max_runs_per_session=MAX_RUNS_PER_SESSION, daily_cap=DAILY_CAP):
    """Decide whether one more run is allowed.

    Returns (allowed, message, new_daily_counts). new_daily_counts only keeps today's count.
    """
    if session_runs_used >= max_runs_per_session:
        return (False,
                f"You've used all {max_runs_per_session} demo runs for this session. "
                "Thanks for trying it! To run more, clone the repo and use your own API key.",
                daily_counts)
    used_today = daily_counts.get(today, 0)
    if used_today >= daily_cap:
        return (False, "The shared daily demo limit has been reached. Please try again tomorrow (UTC).",
                daily_counts)
    return (True, None, {today: used_today + 1})
