# Emy-FullStack Deployment Guide

## Hostinger Ubuntu VPS Deployment

### Prerequisites
- Hostinger VPS with Ubuntu 25.10
- SSH access to your server
- Domain name (optional, for HTTPS)

---

## Quick Start

### Step 1: Initial Server Setup

SSH into your Hostinger VPS:
```bash
ssh root@YOUR_SERVER_IP
```

Download and run the setup script:
```bash
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/deploy/setup-server.sh
chmod +x setup-server.sh
sudo bash setup-server.sh
```

Or manually copy and run:
```bash
scp deploy/setup-server.sh root@YOUR_SERVER_IP:/tmp/
ssh root@YOUR_SERVER_IP 'bash /tmp/setup-server.sh'
```

### Step 2: Deploy Application

From your local machine:
```bash
# Make deploy script executable
chmod +x deploy/deploy.sh

# Deploy to server
./deploy/deploy.sh YOUR_SERVER_IP emyagent
```

Or deploy as root:
```bash
./deploy/deploy.sh YOUR_SERVER_IP root
```

---

## Manual Deployment

### 1. Set Up Server Manually

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose plugin
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 2. Upload Files

```bash
# From local machine
scp -r ./* emyagent@YOUR_SERVER_IP:/opt/emy-fullstack/
```

### 3. Configure Environment

On the server:
```bash
cd /opt/emy-fullstack

# Create .env from production template
cp deploy/.env.production .env

# Edit with your values
nano .env
```

Update these values:
- `OPENAI_API_KEY` - Your OpenAI API key
- `POSTGRES_PASSWORD` - Strong database password
- `SECRET_KEY` - Random 64-character string
- `OPENCLAW_API_KEY` - Your API authentication key

### 4. Start Services

```bash
cd /opt/emy-fullstack
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f openclaw
```

---

## Set Up HTTPS with Nginx (Optional)

### 1. Install Nginx and Certbot

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

### 2. Configure Nginx

```bash
# Copy nginx config
sudo cp /opt/emy-fullstack/deploy/nginx.conf /etc/nginx/sites-available/emy-fullstack

# Edit and replace 'your-domain.com' with your domain
sudo nano /etc/nginx/sites-available/emy-fullstack

# Enable site
sudo ln -s /etc/nginx/sites-available/emy-fullstack /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 3. Get SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

---

## Management Commands

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f openclaw
docker compose logs -f worker
```

### Restart Services
```bash
docker compose restart

# Restart specific service
docker compose restart openclaw
```

### Stop Services
```bash
docker compose down
```

### Update Deployment
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build
```

### View Resource Usage
```bash
docker stats
```

---

## Systemd Service (Auto-start on Boot)

The setup script creates a systemd service. To manage it:

```bash
# Start service
sudo systemctl start emy-fullstack

# Stop service
sudo systemctl stop emy-fullstack

# Enable auto-start on boot
sudo systemctl enable emy-fullstack

# Check status
sudo systemctl status emy-fullstack
```

---

## Firewall Configuration

The setup script configures UFW firewall:

```bash
# Check status
sudo ufw status

# Allow additional ports
sudo ufw allow 443/tcp

# Check logs
sudo tail -f /var/log/ufw.log
```

---

## Monitoring

### Enable Flower (Celery Monitor)
```bash
docker compose --profile monitoring up -d
```
Access at: `http://YOUR_SERVER_IP:5555`

### Health Check
```bash
curl http://YOUR_SERVER_IP:8080/health
```

### API Status
```bash
curl http://YOUR_SERVER_IP:8080/status
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs openclaw

# Check container status
docker compose ps -a
```

### Port already in use
```bash
# Find process using port
sudo lsof -i :8080
sudo kill -9 <PID>
```

### Permission issues
```bash
sudo chown -R emyagent:emyagent /opt/emy-fullstack
```

### Out of memory
```bash
# Check memory
free -h

# Check Docker memory usage
docker stats --no-stream
```

---

## Security Best Practices

1. **Change default passwords** in `.env`
2. **Enable UFW firewall** (done by setup script)
3. **Use HTTPS** in production
4. **Rotate API keys** periodically
5. **Enable fail2ban** (done by setup script)
6. **Keep system updated**: `sudo apt update && sudo apt upgrade`

---

## API Endpoints

Once deployed, your API will be available at:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /status` | System status |
| `GET /agents` | List all agents |
| `POST /command` | Execute command |
| `POST /projects/create` | Create new project |
| `POST /generate/code` | Generate code |

Full API docs: `http://YOUR_SERVER_IP:8080/docs`
