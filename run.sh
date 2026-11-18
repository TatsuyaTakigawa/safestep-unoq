#!/bin/bash
# Run SafeStep on the UNO Q (no Docker).
#   ./run.sh               detection + alarm player (foreground, Ctrl+C to stop)
#   ./run.sh test-camera   save camera_test.jpg
#   ./run.sh test-audio    play the alarm sound once
#   ./run.sh observe       print tracked positions (to decide LINE_Y)
#   ./run.sh line-test     print line crossings only
#   ./run.sh audio-list    list sound cards
# Settings are environment variables, e.g.  SAFESTEP_LINE_Y=200 SAFESTEP_NORMAL_DIRECTION=UP ./run.sh
#   SAFESTEP_CAMERA (auto|N), SAFESTEP_AUDIO_DEVICE (e.g. plughw:1,0), SAFESTEP_LINE_Y, SAFESTEP_MARGIN,
#   SAFESTEP_NORMAL_DIRECTION, SAFESTEP_REVERSE_WINDOW_SEC, SAFESTEP_REVERSE_THRESHOLD,
#   SAFESTEP_ALARM_COOLDOWN_SEC, SAFESTEP_GAP_SEC
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$DIR/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "Run ./setup.sh first."
    exit 1
fi
cd "$DIR/app" || exit 1
export PYTHONUNBUFFERED=1
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$HOME/.config/Ultralytics}"

CMD="${1:-run}"
case "$CMD" in
  run)
    "$PY" -u alarm_player.py &
    PLAYER_PID=$!
    sleep 1
    if ! kill -0 "$PLAYER_PID" 2>/dev/null; then
        echo "WARNING: the alarm player did not start. Detection will run without sound."
        PLAYER_PID=""
    fi

    "$PY" -u safestep_run.py &
    DETECT_PID=$!

    cleanup() {
        kill "$DETECT_PID" 2>/dev/null
        [ -n "$PLAYER_PID" ] && kill "$PLAYER_PID" 2>/dev/null
        wait 2>/dev/null
    }
    trap 'cleanup; exit 0' TERM INT

    wait "$DETECT_PID"
    STATUS=$?
    [ -n "$PLAYER_PID" ] && kill "$PLAYER_PID" 2>/dev/null
    exit "$STATUS"
    ;;
  test-audio)  exec "$PY" -u alarm_player.py --test ;;
  test-camera) exec "$PY" -u camera_test.py ;;
  observe)     exec "$PY" -u observe.py ;;
  line-test)   exec "$PY" -u line_test.py ;;
  audio-list)  aplay -l; echo; cat /proc/asound/cards 2>/dev/null ;;
  *)           echo "Unknown command: $CMD"; sed -n '2,12p' "$DIR/run.sh"; exit 1 ;;
esac
