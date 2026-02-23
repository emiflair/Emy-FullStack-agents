#!/bin/bash
# =============================================================================
# Emy-FullStack Server Setup Script for Ubuntu (Hostinger VPS)
# =============================================================================
#
# This script sets up a fresh Ubuntu server with Docker and all dependencies
# needed to run the Emy-FullStack AI Agent System.
#
# Usage: 
#   sudo bash setup-server.sh
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ${GREEN}Emy-FullStack Server Setup${BLUE}                                 ║${NC}"
echo -e "${BLUE}║     ${YELLOW}Hostinger Ubuntu VPS${BLUE}                                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (sudo bash setup-server.sh)${NC}"
    exit 1
fi

# =============================================================================
# System Update
# =============================================================================
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt-get update && apt-get upgrade -y

# =============================================================================
# Install Required Packages
# =============================================================================
echo -e "${YELLOW}📦 Installing required packages...${NC}"
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    fail2ban \
    htop \
    nano

# =============================================================================
# Install Docker
# =============================================================================
echo -e "${YELLOW}🐳 Installing Docker...${NC}"

# Remove old versions
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

echo -e "${GREEN}✅ Docker installed successfully${NC}"
docker --version
docker compose version

# =============================================================================
# Configure Firewall
# =============================================================================
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"

ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # API (can be removed if using reverse proxy)

# Enable firewall
echo "y" | ufw enable
ufw status

echo -e "${GREEN}✅ Firewall configured${NC}"

# =============================================================================
# Configure Fail2Ban
# =============================================================================
echo -e "${YELLOW}🛡️ Configuring Fail2Ban...${NC}"

systemctl start fail2ban
systemctl enable fail2ban

echo -e "${GREEN}✅ Fail2Ban configured${NC}"

# =============================================================================
# Create Application User
# =============================================================================
echo -e "${YELLOW}👤 Creating application user...${NC}"

# Create user if doesn't exist
if ! id "emyagent" &>/dev/null; then
    useradd -m -s /bin/bash -G docker emyagent
    echo -e "${GREEN}✅ User 'emyagent' created${NC}"
else
    echo -e "${YELLOW}⚠️ User 'emyagent' already exists${NC}"
    usermod -aG docker emyagent
fi

# =============================================================================
# Create Application Directory
# =============================================================================
echo -e "${YELLOW}📁 Creating application directory...${NC}"

mkdir -p /opt/emy-fullstack
mkdir -p /opt/emy-fullstack/projects
mkdir -p /opt/emy-fullstack/logs
chown -R emyagent:emyagent /opt/emy-fullstack

echo -e "${GREEN}✅ Directory /opt/emy-fullstack created${NC}"

# =============================================================================
# Create Systemd Service
# =============================================================================
echo -e "${YELLOW}⚙️ Creating systemd service...${NC}"

cat > /etc/systemd/system/emy-fullstack.service << 'EOF'
[Unit]
Description=Emy-FullStack AI Agent System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=emyagent
Group=emyagent
WorkingDirectory=/opt/emy-fullstack
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable emy-fullstack

echo -e "${GREEN}✅ Systemd service created${NC}"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Server Setup Complete!                                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Upload your project to /opt/emy-fullstack/"
echo -e "2. Create .env file with your OpenAI API key"
echo -e "3. Run: ${YELLOW}sudo systemctl start emy-fullstack${NC}"
echo ""
echo -e "${BLUE}Quick deploy command from your local machine:${NC}"
echo -e "${YELLOW}scp -r ./* emyagent@YOUR_SERVER_IP:/opt/emy-fullstack/${NC}"
echo ""
