#!/usr/bin/env bash
# Detached driver for eval v2 (box only). Needs AICREDITS_API_KEY in the environment; never prints it.
# Start:     setsid nohup scripts/eval_v2_driver.sh >/dev/null 2>&1 &
# Watchdog (cron fallback, restarts only if not running and no STATUS.json):
#   @reboot   /workspace/crm-eval-v2/code/scripts/eval_v2_driver.sh --watchdog
#   */30 * * * * /workspace/crm-eval-v2/code/scripts/eval_v2_driver.sh --watchdog
set -u
OUT=${EVAL_V2_OUT:-/workspace/crm-eval-v2}
CODE="$(cd "$(dirname "$0")/.." && pwd)"
PY=${EVAL_V2_PY:-$OUT/venv/bin/python}
PIDFILE="$OUT/driver.pid"
mkdir -p "$OUT"
if [ "${1:-}" = "--watchdog" ]; then
  [ -f "$OUT/STATUS.json" ] && exit 0
  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then exit 0; fi
  [ -z "${AICREDITS_API_KEY:-}" ] && { echo "$(date -Is) watchdog: no AICREDITS_API_KEY in env, not starting" >> "$OUT/driver.log"; exit 1; }
  setsid nohup "$0" >/dev/null 2>&1 &
  exit 0
fi
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then echo "already running"; exit 0; fi
echo $$ > "$PIDFILE"
cd "$CODE" && exec "$PY" -u eval/eval_v2.py --out "$OUT" --driver >> "$OUT/driver.log" 2>&1
