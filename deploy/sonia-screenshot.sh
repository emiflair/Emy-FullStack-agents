#!/bin/bash
# Sonia Screenshot Tool
# Usage: sonia-screenshot "https://example.com" [filename]

URL="$1"
FILENAME="${2:-screenshot_$(date +%Y%m%d_%H%M%S).png}"
SCREENSHOT_DIR="/tmp/screenshots"
SNAP_TMP="/tmp/snap-private-tmp/snap.chromium/tmp"

mkdir -p "$SCREENSHOT_DIR"

if [ -z "$URL" ]; then
    echo "Usage: sonia-screenshot <url> [filename]"
    exit 1
fi

FILEPATH="$SCREENSHOT_DIR/$FILENAME"

echo "Taking screenshot of $URL..."

# Use chromium in headless mode to take screenshot (saves to snap sandbox)
cd /tmp
/snap/bin/chromium --headless=new --no-sandbox --disable-gpu \
    --screenshot="$FILENAME" \
    --window-size=1920,1080 \
    --hide-scrollbars \
    "$URL" 2>/dev/null

# Copy from snap sandbox to accessible location
if [ -f "$SNAP_TMP/$FILENAME" ]; then
    cp "$SNAP_TMP/$FILENAME" "$FILEPATH"
    rm -f "$SNAP_TMP/$FILENAME"
fi

if [ -f "$FILEPATH" ]; then
    echo "Screenshot saved: $FILEPATH"
    echo "$FILEPATH"
    exit 0
else
    echo "Failed to take screenshot"
    exit 1
fi
