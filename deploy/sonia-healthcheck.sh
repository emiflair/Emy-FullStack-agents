#!/bin/bash
# Sonia Self-Healing Health Check System
# Monitors all services and auto-repairs issues

ISSUES=""
FIXED=""

echo "=== Sonia Health Check $(date) ==="

# 1. Docker
echo -n "Docker: "
if docker ps 2>&1 | grep -q "unhealthy\|Exited"; then
    echo "[FIXING]"
    cd /opt/emy-fullstack && docker-compose up -d 2>/dev/null
    FIXED="$FIXED Docker;"
else
    echo "[OK]"
fi

# 2. Chrome CDP
echo -n "Chrome CDP: "
if curl -s -m 3 http://127.0.0.1:9222/json/version 2>/dev/null | grep -q Browser; then
    echo "[OK]"
else
    echo "[FIXING]"
    systemctl restart chrome-cdp 2>/dev/null
    sleep 2
    FIXED="$FIXED ChromeCDP;"
fi

# 3. OpenClaw
echo -n "OpenClaw: "
if pgrep -f "openclaw" >/dev/null; then
    echo "[OK]"
else
    echo "[FIXING]"
    systemctl restart openclaw 2>/dev/null
    sleep 3
    FIXED="$FIXED OpenClaw;"
fi

# 4. WhatsApp
echo -n "WhatsApp: "
WA_STATUS=$(openclaw channels status 2>&1 | grep -i whatsapp)
if echo "$WA_STATUS" | grep -qi "connected\|linked\|OK"; then
    echo "[OK]"
else
    echo "[NEEDS ATTENTION]"
    ISSUES="$ISSUES WhatsApp-disconnected;"
fi

# 5. Email IMAP
echo -n "Email IMAP: "
if timeout 5 himalaya account list 2>&1 | grep -q sonia; then
    echo "[OK]"
else
    echo "[CHECK]"
    ISSUES="$ISSUES Email-IMAP;"
fi

# 6. Disk Space
DISK_PCT=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
echo -n "Disk ($DISK_PCT%): "
if [ "$DISK_PCT" -gt 90 ]; then
    echo "[FIXING]"
    docker system prune -f 2>/dev/null
    journalctl --vacuum-time=3d 2>/dev/null
    FIXED="$FIXED Disk-cleanup;"
else
    echo "[OK]"
fi

# 7. Memory
MEM_FREE=$(free -m | awk '/^Mem:/{print $7}')
echo -n "Memory (${MEM_FREE}MB free): "
if [ "$MEM_FREE" -lt 100 ]; then
    echo "[LOW]"
    ISSUES="$ISSUES Low-memory;"
else
    echo "[OK]"
fi

# 8. Emy API
echo -n "Emy API: "
if curl -s -m 3 http://localhost:8080/health 2>/dev/null | grep -qi "status\|healthy"; then
    echo "[OK]"
else
    echo "[FIXING]"
    cd /opt/emy-fullstack && docker-compose restart app 2>/dev/null
    sleep 5
    FIXED="$FIXED EmyAPI;"
fi

# 9. Nginx (if running)
echo -n "Nginx: "
if systemctl is-active nginx >/dev/null 2>&1; then
    echo "[OK]"
elif systemctl is-enabled nginx >/dev/null 2>&1; then
    echo "[FIXING]"
    systemctl start nginx 2>/dev/null
    FIXED="$FIXED Nginx;"
else
    echo "[NOT INSTALLED]"
fi

echo "---"
if [ -n "$FIXED" ]; then
    echo "Auto-fixed: $FIXED"
fi
if [ -n "$ISSUES" ]; then
    echo "Needs attention: $ISSUES"
    exit 1
fi
if [ -z "$FIXED" ] && [ -z "$ISSUES" ]; then
    echo "All systems healthy!"
fi
exit 0
