#!/bin/bash
# Sonia Quick Setup Script
# Run this after cloning the repo on a new server
# Usage: bash deploy/quick-setup.sh

set -e

echo "=========================================="
echo "   Sonia Quick Setup - Full Deployment"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash deploy/quick-setup.sh"
    exit 1
fi

# Variables (set these before running)
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_USER_ID="${TELEGRAM_USER_ID:-6116923763}"
EMAIL_ADDRESS="${EMAIL_ADDRESS:-sonia@wazhop.com}"
EMAIL_PASSWORD="${EMAIL_PASSWORD:-}"

# Check required vars
if [ -z "$OPENAI_API_KEY" ]; then
    read -p "Enter OPENAI_API_KEY: " OPENAI_API_KEY
fi

echo ""
echo "Step 1: System packages..."
apt update && apt install -y docker.io docker-compose chromium-browser msmtp msmtp-mta curl jq

echo ""
echo "Step 2: Docker setup..."
systemctl enable docker
systemctl start docker

echo ""
echo "Step 3: Application deployment..."
DEPLOY_DIR="/opt/emy-fullstack"
mkdir -p $DEPLOY_DIR
cp -r . $DEPLOY_DIR/
cd $DEPLOY_DIR

# Create .env
cat > .env << EOF
OPENAI_API_KEY=$OPENAI_API_KEY
POSTGRES_PASSWORD=emy_secure_password_2024
REDIS_PASSWORD=emy_redis_secure_2024
EOF

# Start containers
docker-compose up -d --build
sleep 10

echo ""
echo "Step 4: OpenClaw installation..."
if ! command -v openclaw &> /dev/null; then
    npm install -g @anthropic/openclaw
fi

echo ""
echo "Step 5: OpenClaw configuration..."
mkdir -p ~/.openclaw/extensions

# Configure OpenClaw
openclaw auth add --provider openai --key "$OPENAI_API_KEY" 2>/dev/null || true
openclaw config set agents.defaults.model.primary "openai/gpt-5.2" 2>/dev/null || true

# Add Telegram if token provided
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    cat ~/.openclaw/openclaw.json | jq ".channels.telegram = {\"botToken\": \"$TELEGRAM_BOT_TOKEN\"}" > /tmp/oc.json
    mv /tmp/oc.json ~/.openclaw/openclaw.json
fi

openclaw doctor --fix 2>/dev/null || true

echo ""
echo "Step 6: Chrome CDP service..."
cat > /etc/systemd/system/chrome-cdp.service << 'EOF'
[Unit]
Description=Chrome CDP Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/chromium-browser --headless --disable-gpu --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --no-sandbox --disable-dev-shm-usage --user-data-dir=/root/.config/chromium-cdp
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chrome-cdp
systemctl start chrome-cdp

echo ""
echo "Step 7: Sonia identity..."
mkdir -p ~/.openclaw/agents/main/agent
cp $DEPLOY_DIR/deploy/SONIA-IDENTITY.md ~/.openclaw/agents/main/agent/IDENTITY.md

echo ""
echo "Step 8: Sonia plugins..."
cp -r $DEPLOY_DIR/sonia-plugin ~/.openclaw/extensions/sonia
cd ~/.openclaw/extensions/sonia && npm install 2>/dev/null || true
openclaw plugins trust sonia 2>/dev/null || true

echo ""
echo "Step 9: Health check & scripts..."
cp $DEPLOY_DIR/deploy/sonia-healthcheck-v2.sh /usr/local/bin/sonia-healthcheck
cp $DEPLOY_DIR/deploy/sonia-screenshot.sh /usr/local/bin/sonia-screenshot
chmod +x /usr/local/bin/sonia-healthcheck /usr/local/bin/sonia-screenshot

# Update Telegram user ID in health check
sed -i "s/TELEGRAM_USER=\"6116923763\"/TELEGRAM_USER=\"$TELEGRAM_USER_ID\"/" /usr/local/bin/sonia-healthcheck

echo ""
echo "Step 10: OpenClaw systemd service..."
cat > /etc/systemd/system/openclaw.service << 'EOF'
[Unit]
Description=OpenClaw Agent Service
After=network.target chrome-cdp.service

[Service]
Type=simple
WorkingDirectory=/root
ExecStart=/usr/bin/env openclaw start --local
Restart=always
RestartSec=5
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/root"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable openclaw
systemctl start openclaw

echo ""
echo "Step 11: Cron jobs..."
(crontab -l 2>/dev/null | grep -v sonia; cat << 'CRON'
*/15 * * * * /usr/local/bin/sonia-healthcheck >> /var/log/sonia-health.log 2>&1
0 20 * * * openclaw message send --channel telegram --target "$TELEGRAM_USER_ID" --message "Good evening! Sonia here with your daily check-in. All systems running smoothly." 2>/dev/null
CRON
) | crontab -

echo ""
echo "Step 12: Email setup (msmtp)..."
if [ -n "$EMAIL_PASSWORD" ]; then
cat > /etc/msmtprc << EOF
defaults
auth           on
tls            on
tls_starttls   on
logfile        /var/log/msmtp.log

account        sonia
host           smtp.zoho.com
port           587
from           $EMAIL_ADDRESS
user           $EMAIL_ADDRESS
password       $EMAIL_PASSWORD

account default : sonia
EOF
chmod 600 /etc/msmtprc

cat > /usr/local/bin/sonia-email << 'EMAILSCRIPT'
#!/bin/bash
TO="$1"
SUBJECT="$2"
BODY="$3"
echo -e "Subject: $SUBJECT\nFrom: sonia@wazhop.com\nTo: $TO\n\n$BODY" | msmtp "$TO"
EMAILSCRIPT
chmod +x /usr/local/bin/sonia-email
fi

echo ""
echo "=========================================="
echo "   Setup Complete!"
echo "=========================================="
echo ""
echo "Services running:"
docker ps --format "  - {{.Names}}: {{.Status}}"
echo ""
echo "Next steps:"
echo "  1. Connect WhatsApp: openclaw channels login --channel whatsapp"
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "  2. Telegram configured - start chat with your bot and run:"
    echo "     openclaw pairing approve telegram <CODE>"
fi
echo "  3. Test: sonia-healthcheck"
echo ""
