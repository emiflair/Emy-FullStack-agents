#!/bin/bash
# =============================================================================
# Emy-FullStack Deployment Script
# =============================================================================
#
# Deploy the Emy-FullStack AI Agent System to Hostinger Ubuntu VPS
#
# Usage:
#   ./deploy.sh [SERVER_IP] [SSH_USER]
#
# Example:
#   ./deploy.sh 192.168.1.100 emyagent
#   ./deploy.sh myserver.hostinger.com root
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
SERVER_IP="${1:-}"
SSH_USER="${2:-emyagent}"
REMOTE_DIR="/opt/emy-fullstack"
SSH_KEY="${SSH_KEY:-}"

# Banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ${GREEN}Emy-FullStack Deployment${BLUE}                                  ║${NC}"
echo -e "${BLUE}║     ${YELLOW}Deploy to Hostinger Ubuntu VPS${BLUE}                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check arguments
if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}❌ Server IP required!${NC}"
    echo ""
    echo "Usage: ./deploy.sh [SERVER_IP] [SSH_USER]"
    echo "Example: ./deploy.sh 192.168.1.100 emyagent"
    exit 1
fi

# SSH options
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi

echo -e "${YELLOW}🎯 Target: ${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}${NC}"
echo ""

# =============================================================================
# Pre-deployment Checks
# =============================================================================
echo -e "${YELLOW}🔍 Running pre-deployment checks...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env with your OPENAI_API_KEY"
    exit 1
fi
echo -e "${GREEN}✅ .env file found${NC}"

# Check if docker-compose.yaml exists
if [ ! -f "docker-compose.yaml" ]; then
    echo -e "${RED}❌ docker-compose.yaml not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ docker-compose.yaml found${NC}"

# Check SSH connection
echo -e "${YELLOW}🔗 Testing SSH connection...${NC}"
if ssh $SSH_OPTS $SSH_USER@$SERVER_IP "echo 'Connected'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to server${NC}"
    echo "Please check your SSH credentials and try again"
    exit 1
fi

# =============================================================================
# Create Remote Directory
# =============================================================================
echo -e "${YELLOW}📁 Creating remote directory...${NC}"
ssh $SSH_OPTS $SSH_USER@$SERVER_IP "mkdir -p $REMOTE_DIR/projects $REMOTE_DIR/logs"

# =============================================================================
# Sync Files
# =============================================================================
echo -e "${YELLOW}📤 Syncing files to server...${NC}"

# Files/directories to exclude
EXCLUDES=(
    ".git"
    ".venv"
    "venv"
    "__pycache__"
    "*.pyc"
    ".env.example"
    "*.log"
    "projects/"
    ".DS_Store"
    "deploy/setup-server.sh"
)

# Build rsync exclude args
EXCLUDE_ARGS=""
for item in "${EXCLUDES[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$item"
done

# Rsync files
rsync -avz --progress \
    $EXCLUDE_ARGS \
    -e "ssh $SSH_OPTS" \
    ./ $SSH_USER@$SERVER_IP:$REMOTE_DIR/

echo -e "${GREEN}✅ Files synced${NC}"

# =============================================================================
# Deploy on Server
# =============================================================================
echo -e "${YELLOW}🚀 Deploying on server...${NC}"

ssh $SSH_OPTS $SSH_USER@$SERVER_IP << 'ENDSSH'
cd /opt/emy-fullstack

echo "Stopping existing containers..."
docker compose down 2>/dev/null || true

echo "Building images..."
docker compose build

echo "Starting services..."
docker compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking health..."
curl -s http://localhost:8080/health || echo "Health check pending..."

echo "Container status:"
docker compose ps
ENDSSH

# =============================================================================
# Post-deployment
# =============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Deployment Complete!                                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Your API is now available at:${NC}"
echo -e "${YELLOW}  http://${SERVER_IP}:8080${NC}"
echo ""
echo -e "${BLUE}Quick commands:${NC}"
echo -e "  View logs:    ssh $SSH_USER@$SERVER_IP 'cd $REMOTE_DIR && docker compose logs -f'"
echo -e "  Restart:      ssh $SSH_USER@$SERVER_IP 'cd $REMOTE_DIR && docker compose restart'"
echo -e "  Stop:         ssh $SSH_USER@$SERVER_IP 'cd $REMOTE_DIR && docker compose down'"
echo ""
