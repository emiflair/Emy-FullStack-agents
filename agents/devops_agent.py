"""
DevOps / Cloud Engineer Agent
Responsible for deploying services, setting up task scheduling,
monitoring, scaling, and infrastructure management.
"""

from typing import Any, Dict, List
from .base_agent import BaseAgent, Task


class DevOpsAgent(BaseAgent):
    """
    DevOps / Cloud Engineer Agent for the Emy-FullStack system.
    
    Capabilities:
    - Deploy backend/frontend/worker agents to cloud
    - Setup task scheduling (Celery / Temporal / cron jobs)
    - Monitor health, scaling, logs
    - Docker containerization
    - CI/CD pipeline setup
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="DevOps Engineer",
            description="Deploys and manages cloud infrastructure and CI/CD",
            capabilities=[
                "deployment",
                "containerization",
                "scheduling",
                "monitoring",
                "scaling",
                "ci_cd",
            ],
            config=config or {}
        )
        self.cloud_provider = config.get("cloud_provider", "aws") if config else "aws"
        self.deployments: List[Dict] = []
        self.containers: List[str] = []

    async def execute_task(self, task: Task) -> Any:
        """Execute a DevOps task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "deployment": self._deploy_services,
            "containerization": self._create_containers,
            "scheduling": self._setup_scheduling,
            "monitoring": self._setup_monitoring,
            "scaling": self._configure_scaling,
            "ci_cd": self._setup_ci_cd,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _deploy_services(self, task: Task) -> Dict[str, Any]:
        """Deploy services to cloud."""
        services = task.metadata.get("services", [])
        environment = task.metadata.get("environment", "production")
        
        self.log(f"Deploying {len(services)} services to {environment}")
        
        # Generate deployment configurations
        k8s_config = self._generate_k8s_deployment(services, environment)
        docker_compose = self._generate_docker_compose(services)
        
        deployment_info = {
            "services": services,
            "environment": environment,
            "kubernetes": k8s_config,
            "docker_compose": docker_compose,
        }
        self.deployments.append(deployment_info)
        
        return deployment_info

    def _generate_k8s_deployment(self, services: List[str], environment: str) -> str:
        """Generate Kubernetes deployment manifests."""
        manifests = []
        
        for service in services:
            manifest = f'''---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service}-deployment
  namespace: emy-fullstack-{environment}
  labels:
    app: {service}
    environment: {environment}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {service}
  template:
    metadata:
      labels:
        app: {service}
    spec:
      containers:
      - name: {service}
        image: emy-fullstack/{service}:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: {service}-config
        - secretRef:
            name: {service}-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {service}-service
  namespace: emy-fullstack-{environment}
spec:
  selector:
    app: {service}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
'''
            manifests.append(manifest)
        
        return "\n".join(manifests)

    def _generate_docker_compose(self, services: List[str]) -> str:
        """Generate Docker Compose configuration."""
        compose = '''version: '3.8'

services:
'''
        for service in services:
            compose += f'''
  {service}:
    build:
      context: ./{service}
      dockerfile: Dockerfile
    image: emy-fullstack/{service}:latest
    container_name: {service}
    restart: unless-stopped
    ports:
      - "8000"
    environment:
      - ENV=production
      - DATABASE_URL=${{DATABASE_URL}}
      - REDIS_URL=${{REDIS_URL}}
    depends_on:
      - postgres
      - redis
    networks:
      - emy-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
        
        compose += '''
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: emy_fullstack
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - emy-network

  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - emy-network

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    networks:
      - emy-network

volumes:
  postgres_data:
  redis_data:

networks:
  emy-network:
    driver: bridge
'''
        return compose

    async def _create_containers(self, task: Task) -> Dict[str, Any]:
        """Create Docker containers."""
        service_name = task.metadata.get("service_name", "service")
        base_image = task.metadata.get("base_image", "python:3.11-slim")
        
        self.log(f"Creating container for: {service_name}")
        
        dockerfile = self._generate_dockerfile(service_name, base_image)
        
        self.containers.append(service_name)
        
        return {
            "service_name": service_name,
            "dockerfile": dockerfile,
        }

    def _generate_dockerfile(self, service_name: str, base_image: str) -> str:
        """Generate Dockerfile."""
        return f'''# Dockerfile for {service_name}
FROM {base_image}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# Set work directory
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \\
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup
RUN chown -R appuser:appgroup $APP_HOME
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    async def _setup_scheduling(self, task: Task) -> Dict[str, Any]:
        """Setup task scheduling."""
        scheduler_type = task.metadata.get("scheduler", "celery")
        tasks_config = task.metadata.get("tasks", [])
        
        self.log(f"Setting up {scheduler_type} scheduler")
        
        if scheduler_type == "celery":
            config = self._generate_celery_config(tasks_config)
        else:
            config = self._generate_cron_config(tasks_config)
        
        return {
            "scheduler": scheduler_type,
            "config": config,
        }

    def _generate_celery_config(self, tasks: List[Dict]) -> str:
        """Generate Celery configuration."""
        return '''"""
Celery configuration for Emy-FullStack
"""
from celery import Celery
from celery.schedules import crontab

app = Celery(
    'emy_fullstack',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
    include=['tasks.worker_tasks', 'tasks.automation_tasks']
)

app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Result backend
    result_expires=3600,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-logs': {
            'task': 'tasks.maintenance.cleanup_logs',
            'schedule': crontab(hour=2, minute=0),
        },
        'aggregate-analytics': {
            'task': 'tasks.analytics.aggregate_daily',
            'schedule': crontab(hour=0, minute=30),
        },
        'health-check': {
            'task': 'tasks.monitoring.health_check',
            'schedule': 300.0,  # every 5 minutes
        },
    },
)

# Task routing
app.conf.task_routes = {
    'tasks.worker_tasks.*': {'queue': 'worker'},
    'tasks.automation_tasks.*': {'queue': 'automation'},
    'tasks.analytics.*': {'queue': 'analytics'},
}

if __name__ == '__main__':
    app.start()
'''

    def _generate_cron_config(self, tasks: List[Dict]) -> str:
        """Generate cron configuration."""
        return '''# Crontab configuration for Emy-FullStack
# Format: minute hour day month weekday command

# Cleanup old logs daily at 2 AM
0 2 * * * /app/scripts/cleanup_logs.sh

# Aggregate analytics daily at 12:30 AM
30 0 * * * /app/scripts/aggregate_analytics.sh

# Health check every 5 minutes
*/5 * * * * /app/scripts/health_check.sh

# Database backup daily at 3 AM
0 3 * * * /app/scripts/backup_db.sh

# Weekly report generation on Mondays at 6 AM
0 6 * * 1 /app/scripts/generate_weekly_report.sh
'''

    async def _setup_monitoring(self, task: Task) -> Dict[str, Any]:
        """Setup monitoring and alerting."""
        monitoring_stack = task.metadata.get("stack", "prometheus")
        
        self.log(f"Setting up {monitoring_stack} monitoring")
        
        prometheus_config = self._generate_prometheus_config()
        grafana_dashboard = self._generate_grafana_dashboard()
        
        return {
            "stack": monitoring_stack,
            "prometheus_config": prometheus_config,
            "grafana_dashboard": grafana_dashboard,
        }

    def _generate_prometheus_config(self) -> str:
        """Generate Prometheus configuration."""
        return '''# Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "alerts/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'workers'
    static_configs:
      - targets: ['worker-1:8000', 'worker-2:8000']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
'''

    def _generate_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration."""
        return {
            "title": "Emy-FullStack Dashboard",
            "panels": [
                {"title": "Request Rate", "type": "graph"},
                {"title": "Error Rate", "type": "graph"},
                {"title": "Response Time", "type": "graph"},
                {"title": "Active Workers", "type": "stat"},
                {"title": "Task Queue Length", "type": "gauge"},
                {"title": "Database Connections", "type": "stat"},
            ]
        }

    async def _configure_scaling(self, task: Task) -> Dict[str, Any]:
        """Configure auto-scaling."""
        min_replicas = task.metadata.get("min_replicas", 2)
        max_replicas = task.metadata.get("max_replicas", 10)
        target_cpu = task.metadata.get("target_cpu", 70)
        
        self.log(f"Configuring scaling: {min_replicas}-{max_replicas} replicas")
        
        hpa_config = self._generate_hpa_config(min_replicas, max_replicas, target_cpu)
        
        return {
            "min_replicas": min_replicas,
            "max_replicas": max_replicas,
            "target_cpu": target_cpu,
            "config": hpa_config,
        }

    def _generate_hpa_config(self, min_replicas: int, max_replicas: int, target_cpu: int) -> str:
        """Generate Kubernetes HPA configuration."""
        return f'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: emy-fullstack
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: {min_replicas}
  maxReplicas: {max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {target_cpu}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
'''

    async def _setup_ci_cd(self, task: Task) -> Dict[str, Any]:
        """Setup CI/CD pipeline."""
        platform = task.metadata.get("platform", "github_actions")
        
        self.log(f"Setting up CI/CD on {platform}")
        
        if platform == "github_actions":
            config = self._generate_github_actions()
        else:
            config = self._generate_gitlab_ci()
        
        return {
            "platform": platform,
            "config": config,
        }

    def _generate_github_actions(self) -> str:
        """Generate GitHub Actions workflow."""
        return '''name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run linting
        run: |
          flake8 .
          black --check .
          
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v4
        with:
          manifests: |
            k8s/deployment.yaml
            k8s/service.yaml
          images: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
'''

    def _generate_gitlab_ci(self) -> str:
        """Generate GitLab CI configuration."""
        return '''stages:
  - test
  - build
  - deploy

variables:
  DOCKER_TLS_CERTDIR: "/certs"

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - flake8 .
    - pytest --cov=.

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  only:
    - main
  script:
    - kubectl apply -f k8s/
'''

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic DevOps tasks."""
        self.log(f"Handling generic DevOps task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic DevOps task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with DevOps-specific info."""
        base_status = super().get_status()
        base_status.update({
            "cloud_provider": self.cloud_provider,
            "deployments": len(self.deployments),
            "containers": self.containers,
        })
        return base_status
