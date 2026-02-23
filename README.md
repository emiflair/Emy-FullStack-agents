# Emy-FullStack AI Developer System

A multi-agent AI system for autonomous full-stack application development, from design to deployment.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Master Brain                             │
│    ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│    │   Optimizer   │  │ Feedback Loop│  │ Agent Coordinator  │  │
│    └───────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Task Queue (Celery + Redis)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Specialized Agents                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Frontend │ │ Backend  │ │ Database │ │  DevOps  │           │
│  │ (Flutter)│ │(FastAPI) │ │(Postgres)│ │  (K8s)   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   QA     │ │  UI/UX   │ │ Security │ │  AI/ML   │           │
│  │ (pytest) │ │(Wireframe│ │  (Auth)  │ │ (OpenAI) │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                       ┌──────────────────┐                      │
│                       │ Project Manager  │                      │
│                       │  (Orchestrator)  │                      │
│                       └──────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OpenClaw Integration                         │
│    ┌───────────┐  ┌────────────┐  ┌────────────────────────┐   │
│    │  Scraper  │  │   Poster   │  │  Automation Engine     │   │
│    └───────────┘  └────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### 9 Specialized AI Agents

| Agent | Responsibility | Tech Stack |
|-------|---------------|------------|
| **Frontend** | UI generation, widgets, state management | Flutter, Riverpod |
| **Backend** | API endpoints, CRUD, authentication | FastAPI, JWT |
| **Database** | Schema design, migrations, caching | PostgreSQL, Redis |
| **DevOps** | CI/CD, containers, deployment | Docker, Kubernetes |
| **QA** | Testing, coverage, automation | pytest, Flutter Test |
| **UI/UX** | Wireframes, design systems, layouts | Material Design |
| **Security** | Auth, encryption, vulnerability scans | OAuth2, AES-256 |
| **AI/ML** | Content generation, predictions | OpenAI GPT-4 |
| **Project Manager** | Sprint planning, task coordination | Agile workflows |

### Master Brain Orchestrator
- **System Optimizer**: Load balancing, priority-based scheduling, cost optimization
- **Feedback Loop**: Real-time analytics, pattern detection, auto-adjustments
- **Agent Coordinator**: Inter-agent messaging, workflow execution, health monitoring

### Task Queue System
- **Celery + Redis**: Distributed task processing
- **Priority Queues**: Critical, High, Medium, Low, Background
- **Task Routing**: Agent-specific queues with dynamic routing

### OpenClaw Integration
- **Web Scraper**: CSS selectors, XPath, regex extraction
- **Content Poster**: Multi-platform posting (Twitter, LinkedIn, etc.)
- **Automation Engine**: Workflow automation with triggers and actions

## 📦 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker (optional)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Emy-FullStack-agents.git
cd Emy-FullStack-agents
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start services**
```bash
# Start Redis
redis-server

# Start PostgreSQL
# (use your preferred method)

# Run database migrations
alembic upgrade head
```

6. **Run the system**
```bash
python main.py
```

## 🐳 Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📁 Project Structure

```
Emy-FullStack-agents/
├── agents/                    # AI Agents
│   ├── __init__.py
│   ├── base_agent.py         # Base agent framework
│   ├── frontend_agent.py     # Flutter UI generation
│   ├── backend_agent.py      # FastAPI endpoints
│   ├── database_agent.py     # PostgreSQL/Redis
│   ├── devops_agent.py       # Docker/K8s
│   ├── qa_agent.py           # Testing
│   ├── uiux_agent.py         # Design/wireframes
│   ├── security_agent.py     # Auth/encryption
│   ├── aiml_agent.py         # AI/ML tasks
│   └── project_manager_agent.py
│
├── config/                    # Configuration
│   ├── __init__.py
│   ├── settings.py           # Main settings
│   ├── database.py           # PostgreSQL config
│   ├── redis_config.py       # Redis config
│   ├── celery_config.py      # Celery config
│   ├── agents_config.py      # Agent settings
│   └── security.py           # Security config
│
├── integrations/              # External integrations
│   └── openclaw/
│       ├── __init__.py
│       ├── client.py         # API client
│       ├── scraper.py        # Web scraping
│       ├── poster.py         # Content posting
│       └── automation.py     # Workflow automation
│
├── master_brain/              # Central orchestrator
│   ├── __init__.py
│   ├── master_brain.py       # Main controller
│   ├── optimizer.py          # System optimization
│   ├── feedback_loop.py      # Analytics & feedback
│   └── agent_coordinator.py  # Agent coordination
│
├── task_queue/                # Task queue system
│   ├── __init__.py
│   ├── celery_app.py         # Celery configuration
│   ├── priority_queue.py     # Priority management
│   ├── task_router.py        # Task routing
│   ├── worker_manager.py     # Worker management
│   └── task_registry.py      # Task registration
│
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | development/staging/production | development |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://... |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENCLAW_API_KEY` | OpenClaw API key | - |
| `SECRET_KEY` | Application secret key | - |

See `.env.example` for full configuration options.

## 📖 Usage

### Starting the System

```python
import asyncio
from main import get_system

async def main():
    system = get_system()
    await system.initialize()
    await system.start()
    
    # Create a new project
    result = await system.create_project(
        project_name="my-app",
        project_type="mobile",
        requirements={
            "features": ["auth", "dashboard", "notifications"],
            "platforms": ["ios", "android"],
        }
    )
    
asyncio.run(main())
```

### Executing Tasks

```python
# Execute a specific task
result = await system.execute_task(
    task_type="generate_api_endpoint",
    task_data={
        "endpoint": "/users",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "authentication": True,
    },
    priority=7,
)
```

### Running Celery Workers

```bash
# Start all workers
celery -A task_queue.celery_app worker -l info -Q default,frontend,backend,database,devops,qa

# Start agent-specific worker
celery -A task_queue.celery_app worker -l info -Q backend -c 4

# Start beat scheduler
celery -A task_queue.celery_app beat -l info
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

## 📊 Monitoring

- **Prometheus metrics**: `http://localhost:9090/metrics`
- **Health endpoint**: `http://localhost:8000/health`
- **System status**: `http://localhost:8000/status`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- FastAPI framework
- Flutter framework
- Celery project
- Redis

---

Built with ❤️ by the Emy-FullStack Team
