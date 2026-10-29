#!/usr/bin/env bash
# Startet ein virtuelles Display im Container, erreichbar im Browser unter
# http://localhost:6080/vnc.html  (ohne Passwort, nur für die lokale Entwicklung).

DISPLAY_NUM="${DISPLAY:-:1}"
RESOLUTION="${DISPLAY_RESOLUTION:-1600x1000x24}"
LOG_DIR="/tmp/display-logs"
mkdir -p "$LOG_DIR"

if xdpyinfo -display "$DISPLAY_NUM" >/dev/null 2>&1; then
    echo "Display $DISPLAY_NUM läuft bereits."
    exit 0
fi

# Prozesse per setsid vom Aufrufer lösen, damit sie das Ende von postStartCommand überleben.
setsid nohup Xvfb "$DISPLAY_NUM" -screen 0 "$RESOLUTION" +extension GLX -nolisten tcp >"$LOG_DIR/xvfb.log" 2>&1 &

for _ in $(seq 1 50); do
    xdpyinfo -display "$DISPLAY_NUM" >/dev/null 2>&1 && break
    sleep 0.1
done

DISPLAY="$DISPLAY_NUM" setsid nohup fluxbox >"$LOG_DIR/fluxbox.log" 2>&1 &
setsid nohup x11vnc -display "$DISPLAY_NUM" -forever -shared -nopw -localhost -rfbport 5900 >"$LOG_DIR/x11vnc.log" 2>&1 &
setsid nohup websockify --web /usr/share/novnc 6080 localhost:5900 >"$LOG_DIR/novnc.log" 2>&1 &

echo "Virtuelles Display $DISPLAY_NUM gestartet: http://localhost:6080/vnc.html"
