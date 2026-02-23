#!/bin/bash
# =============================================================================
# Emy-FullStack AI Agent System - Startup Script
# =============================================================================
#
# This script starts the OpenClaw Control Plane which controls all agents.
#
# Usage:
#   ./start.sh                    # Start locally (development)
#   ./start.sh --docker           # Start with Docker (production)
#   ./start.sh --cloud            # Build and push for cloud deployment
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║     ${GREEN}Emy-FullStack AI Agent System${BLUE}                             ║${NC}"
echo -e "${BLUE}║     ${YELLOW}OpenClaw Control Plane${BLUE}                                   ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# Environment Check
# =============================================================================

check_environment() {
    echo -e "${YELLOW}Checking environment...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3 found${NC}"
    
    # Check OpenAI API Key
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set. AI code generation will be disabled.${NC}"
        echo -e "${YELLOW}   Set it with: export OPENAI_API_KEY=sk-your-key${NC}"
    else
        echo -e "${GREEN}✅ OPENAI_API_KEY configured${NC}"
    fi
    
    # Check OpenClaw API Key
    if [ -z "$OPENCLAW_API_KEY" ]; then
        export OPENCLAW_API_KEY="emy-local-dev-key"
        echo -e "${YELLOW}⚠️  OPENCLAW_API_KEY not set. Using default: ${OPENCLAW_API_KEY}${NC}"
    else
        echo -e "${GREEN}✅ OPENCLAW_API_KEY configured${NC}"
    fi
    
    echo ""
}

# =============================================================================
# Install Dependencies
# =============================================================================

install_deps() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
    echo ""
}

# =============================================================================
# Start Local Development Server
# =============================================================================

start_local() {
    check_environment
    
    echo -e "${YELLOW}Starting OpenClaw Control Plane (Development Mode)...${NC}"
    echo ""
    echo -e "${GREEN}API Documentation:${NC} http://localhost:8080/docs"
    echo -e "${GREEN}Health Check:${NC}      http://localhost:8080/health"
    echo -e "${GREEN}System Status:${NC}     http://localhost:8080/status"
    echo ""
    echo -e "${BLUE}To control the agents from another terminal:${NC}"
    echo ""
    echo "  # Create a project"
    echo "  curl -X POST http://localhost:8080/project/create \\"
    echo "    -H 'X-API-Key: $OPENCLAW_API_KEY' \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"name\": \"MyApp\", \"project_type\": \"fullstack\"}'"
    echo ""
    echo "  # Check system status"
    echo "  curl http://localhost:8080/status -H 'X-API-Key: $OPENCLAW_API_KEY'"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    # Start the server
    python -m uvicorn integrations.openclaw.control_plane:app --host 0.0.0.0 --port 8080 --reload
}

# =============================================================================
# Start with Docker
# =============================================================================

start_docker() {
    echo -e "${YELLOW}Starting with Docker Compose...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker found${NC}"
    echo ""
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env and set your OPENAI_API_KEY${NC}"
    fi
    
    # Build and start
    echo -e "${YELLOW}Building containers...${NC}"
    docker compose build
    
    echo -e "${YELLOW}Starting services...${NC}"
    docker compose up -d
    
    echo ""
    echo -e "${GREEN}✅ Services started!${NC}"
    echo ""
    echo -e "OpenClaw Control Plane: ${GREEN}http://localhost:8080${NC}"
    echo -e "API Documentation:      ${GREEN}http://localhost:8080/docs${NC}"
    echo -e "Celery Flower:          ${GREEN}http://localhost:5555${NC} (with --profile monitoring)"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  docker compose logs -f openclaw    # View control plane logs"
    echo "  docker compose logs -f worker      # View worker logs"
    echo "  docker compose ps                  # List running services"
    echo "  docker compose down                # Stop all services"
    echo ""
}

# =============================================================================
# Build for Cloud Deployment
# =============================================================================

build_cloud() {
    echo -e "${YELLOW}Building for cloud deployment...${NC}"
    
    REGISTRY=${DOCKER_REGISTRY:-""}
    IMAGE_NAME=${IMAGE_NAME:-"emy-fullstack"}
    TAG=${TAG:-"latest"}
    
    if [ -z "$REGISTRY" ]; then
        echo -e "${YELLOW}No DOCKER_REGISTRY set. Building local image only.${NC}"
        IMAGE_FULL="$IMAGE_NAME:$TAG"
    else
        IMAGE_FULL="$REGISTRY/$IMAGE_NAME:$TAG"
    fi
    
    echo -e "${YELLOW}Building image: $IMAGE_FULL${NC}"
    docker build -t $IMAGE_FULL .
    
    if [ -n "$REGISTRY" ]; then
        echo -e "${YELLOW}Pushing to registry...${NC}"
        docker push $IMAGE_FULL
        echo -e "${GREEN}✅ Image pushed: $IMAGE_FULL${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Build complete!${NC}"
    echo ""
    echo -e "${BLUE}Deploy to your cloud provider:${NC}"
    echo ""
    echo "  # AWS ECS / Fargate"
    echo "  aws ecs update-service --cluster my-cluster --service emy-agents --force-new-deployment"
    echo ""
    echo "  # Google Cloud Run"
    echo "  gcloud run deploy emy-agents --image $IMAGE_FULL --platform managed"
    echo ""
    echo "  # Azure Container Apps"
    echo "  az containerapp update -n emy-agents -g my-resource-group --image $IMAGE_FULL"
    echo ""
    echo "  # Kubernetes"
    echo "  kubectl set image deployment/emy-agents openclaw=$IMAGE_FULL"
    echo ""
}

# =============================================================================
# Show Help
# =============================================================================

show_help() {
    echo "Usage: ./start.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no option)     Start locally for development"
    echo "  --docker        Start with Docker Compose (production)"
    echo "  --cloud         Build Docker image for cloud deployment"
    echo "  --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY       Your OpenAI API key (required for AI generation)"
    echo "  OPENCLAW_API_KEY     API key for authenticating requests to control plane"
    echo "  DOCKER_REGISTRY      Docker registry URL (for --cloud)"
    echo "  IMAGE_NAME           Docker image name (default: emy-fullstack)"
    echo "  TAG                  Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  # Development"
    echo "  export OPENAI_API_KEY=sk-your-key"
    echo "  ./start.sh"
    echo ""
    echo "  # Production with Docker"
    echo "  ./start.sh --docker"
    echo ""
    echo "  # Build and push to registry"
    echo "  DOCKER_REGISTRY=gcr.io/my-project ./start.sh --cloud"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

case "${1:-}" in
    --docker)
        start_docker
        ;;
    --cloud)
        build_cloud
        ;;
    --help|-h)
        show_help
        ;;
    *)
        install_deps
        start_local
        ;;
esac
