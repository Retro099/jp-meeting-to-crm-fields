from demo_limits import DAILY_CAP, MAX_CHARS, MAX_RUNS_PER_SESSION, reserve_run, validate_note


def test_constants():
    assert (MAX_CHARS, MAX_RUNS_PER_SESSION, DAILY_CAP) == (2000, 5, 50)


def test_validate_note():
    assert validate_note("商談メモ") is None
    assert validate_note("あ" * MAX_CHARS) is None
    assert validate_note("")[0] == "warning"
    assert validate_note("   \n")[0] == "warning"
    level, msg = validate_note("あ" * (MAX_CHARS + 1))
    assert level == "error" and str(MAX_CHARS) in msg


def test_session_cap():
    counts = {}
    for used in range(MAX_RUNS_PER_SESSION):
        allowed, msg, counts = reserve_run(used, counts, "2026-09-30")
        assert allowed and msg is None
    allowed, msg, new_counts = reserve_run(MAX_RUNS_PER_SESSION, counts, "2026-09-30")
    assert not allowed and "5 demo runs" in msg
    assert new_counts == counts == {"2026-09-30": MAX_RUNS_PER_SESSION}


def test_daily_cap_and_reset():
    full = {"2026-09-30": DAILY_CAP}
    allowed, msg, counts = reserve_run(0, full, "2026-09-30")
    assert not allowed and "daily" in msg and counts == full
    allowed, msg, counts = reserve_run(0, full, "2026-10-01")  # new UTC day
    assert allowed and counts == {"2026-10-01": 1}
