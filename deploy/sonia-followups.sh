#!/bin/bash
# Sonia Follow-up Processor
# Run this via cron to process due reminders

DB_PATH="/opt/emy-fullstack/sonia-workspace/sonia_tasks.db"
LOG_FILE="/var/log/sonia-followups.log"

echo "=== Follow-up Check $(date) ===" >> "$LOG_FILE"

# Get due follow-ups
FOLLOWUPS=$(sqlite3 -separator '|' "$DB_PATH" "SELECT id, contact, channel, message FROM follow_ups WHERE sent=0 AND remind_at <= datetime('now')" 2>/dev/null)

if [ -z "$FOLLOWUPS" ]; then
    echo "No due follow-ups" >> "$LOG_FILE"
    exit 0
fi

# Process each follow-up
while IFS='|' read -r id contact channel message; do
    echo "Processing follow-up $id: $message" >> "$LOG_FILE"
    
    # Send via appropriate channel
    if [ "$channel" = "telegram" ]; then
        openclaw message send --channel telegram --target "$contact" --message "$message" 2>/dev/null
    elif [ "$channel" = "email" ]; then
        echo -e "Subject: Reminder\nFrom: sonia@wazhop.com\nTo: $contact\n\n$message" | msmtp "$contact" 2>/dev/null
    else
        openclaw message send --channel whatsapp --message "$message" 2>/dev/null
    fi
    
    # Mark as sent
    sqlite3 "$DB_PATH" "UPDATE follow_ups SET sent=1 WHERE id=$id"
    echo "Sent follow-up $id via $channel" >> "$LOG_FILE"
    
done <<< "$FOLLOWUPS"

echo "Done" >> "$LOG_FILE"
