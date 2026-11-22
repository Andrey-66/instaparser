#!/bin/sh
# Delay file persisted on the /content mount so it survives container restarts
=/content/.parser_restart_delay
MAX_DELAY=18000  # 5 hours

if [ -f "$DELAY_FILE" ]; then
    DELAY=$(cat "$DELAY_FILE")
    echo "[restart_wrapper] Waiting ${DELAY}s before starting parser (avoiding Instagram IP ban)..."
    python -m app_parser.utils.activity "$DELAY"
    sleep "$DELAY"
    NEW_DELAY=$(( DELAY * 2 ))
    [ "$NEW_DELAY" -gt "$MAX_DELAY" ] && NEW_DELAY="$MAX_DELAY"
    echo "$NEW_DELAY" > "$DELAY_FILE"
else
    # First run — start immediately, set 1h delay for the next restart
    echo 3600 > "$DELAY_FILE"
fi

python run.py
EXIT_CODE=$?
rm -f /content/.parser_status.json

if [ "$EXIT_CODE" -eq 0 ]; then
    rm -f "$DELAY_FILE"
fi

exit "$EXIT_CODE"
