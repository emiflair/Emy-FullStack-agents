"""
Emy-FullStack AI Developer System
Main Orchestrator Entry Point

This is the main entry point for the Emy-FullStack AI agent system.
It initializes all agents, sets up communication channels, starts the
Master Brain, and connects the task queue for autonomous application development.
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# Configuration
from config import (
    Settings, get_settings, Environment,
    DatabaseConfig, RedisConfig, CelerySettings,
    AgentsConfig, SecurityConfig,
)
from config.agents_config import AgentType, get_agents_config
from config.database import get_database_config
from config.redis_config import get_redis_config
from config.celery_config import get_celery_settings

# Agents
from agents import (
    FrontendAgent, BackendAgent, DatabaseAgent,
    DevOpsAgent, QAAgent, UIUXAgent,
    SecurityAgent, AIMLAgent, ProjectManagerAgent,
)
from agents.base_agent import AgentCommunicator

# Task Queue
from task_queue import (
    celery_app, TaskRouter, PriorityTaskQueue,
    WorkerManager, TaskRegistry,
)

# Master Brain
from master_brain import (
    MasterBrain, SystemOptimizer, FeedbackLoop,
    AgentCoordinator, BrainState,
)

# OpenClaw Integration
from integrations.openclaw import (
    OpenClawClient, OpenClawConfig,
    WebScraper, ContentPoster, AutomationEngine,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('emy_fullstack.log'),
    ]
)
logger = logging.getLogger('emy-fullstack')


class EmyFullStackSystem:
    """
    Main orchestrator for the Emy-FullStack AI Developer System
    
    Coordinates all components:
    - 9 Specialized AI Agents
    - Master Brain for optimization
    - Task Queue for parallel execution
    - OpenClaw for external integrations
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.agents_config = get_agents_config()
        
        # System state
        self._running = False
        self._start_time: Optional[datetime] = None
        
        # Components
        self.agents: Dict[AgentType, Any] = {}
        self.master_brain: Optional[MasterBrain] = None
        self.coordinator: Optional[AgentCoordinator] = None
        self.optimizer: Optional[SystemOptimizer] = None
        self.feedback_loop: Optional[FeedbackLoop] = None
        self.task_router: Optional[TaskRouter] = None
        self.priority_queue: Optional[PriorityTaskQueue] = None
        self.worker_manager: Optional[WorkerManager] = None
        self.communicator: Optional[AgentCommunicator] = None
        
        # OpenClaw
        self.openclaw_client: Optional[OpenClawClient] = None
        self.web_scraper: Optional[WebScraper] = None
        self.content_poster: Optional[ContentPoster] = None
        self.automation_engine: Optional[AutomationEngine] = None
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
    
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing Emy-FullStack AI Developer System...")
        
        # Initialize communication layer
        await self._init_communication()
        
        # Initialize agents
        await self._init_agents()
        
        # Initialize Master Brain
        await self._init_master_brain()
        
        # Initialize task queue
        await self._init_task_queue()
        
        # Initialize OpenClaw
        await self._init_openclaw()
        
        logger.info("System initialization complete!")
    
    async def _init_communication(self):
        """Initialize inter-agent communication"""
        logger.info("Setting up communication layer...")
        
        redis_config = get_redis_config()
        self.communicator = AgentCommunicator(redis_config.cache_url)
    
    async def _init_agents(self):
        """Initialize all specialized agents"""
        logger.info("Initializing agents...")
        
        agent_classes = {
            AgentType.FRONTEND: FrontendAgent,
            AgentType.BACKEND: BackendAgent,
            AgentType.DATABASE: DatabaseAgent,
            AgentType.DEVOPS: DevOpsAgent,
            AgentType.QA: QAAgent,
            AgentType.UIUX: UIUXAgent,
            AgentType.SECURITY: SecurityAgent,
            AgentType.AIML: AIMLAgent,
            AgentType.PROJECT_MANAGER: ProjectManagerAgent,
        }
        
        for agent_type, agent_class in agent_classes.items():
            config = self.agents_config.get_agent(agent_type)
            
            if config and config.enabled:
                try:
                    agent = agent_class(
                        agent_id=f"{agent_type.value}_agent",
                        name=config.name,
                    )
                    self.agents[agent_type] = agent
                    logger.info(f"  - {config.name} initialized")
                except Exception as e:
                    logger.error(f"  - Failed to initialize {agent_type.value}: {e}")
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    async def _init_master_brain(self):
        """Initialize Master Brain and related components"""
        logger.info("Initializing Master Brain...")
        
        # System Optimizer
        self.optimizer = SystemOptimizer()
        logger.info("  - System Optimizer ready")
        
        # Feedback Loop
        self.feedback_loop = FeedbackLoop()
        logger.info("  - Feedback Loop ready")
        
        # Agent Coordinator
        self.coordinator = AgentCoordinator()
        
        # Register agents with coordinator
        for agent_type, agent in self.agents.items():
            self.coordinator.register_agent(
                agent_id=agent.agent_id,
                agent_type=agent_type.value,
                capabilities=agent.capabilities if hasattr(agent, 'capabilities') else [],
            )
        logger.info("  - Agent Coordinator ready")
        
        # Master Brain
        self.master_brain = MasterBrain(
            brain_id="master_brain_primary",
            optimizer=self.optimizer,
            feedback_loop=self.feedback_loop,
            coordinator=self.coordinator,
        )
        logger.info("  - Master Brain ready")
    
    async def _init_task_queue(self):
        """Initialize task queue system"""
        logger.info("Initializing task queue...")
        
        celery_settings = get_celery_settings()
        redis_config = get_redis_config()
        
        # Task Router
        self.task_router = TaskRouter()
        logger.info("  - Task Router ready")
        
        # Priority Queue
        self.priority_queue = PriorityTaskQueue(redis_config.get_url())
        logger.info("  - Priority Queue ready")
        
        # Worker Manager
        self.worker_manager = WorkerManager()
        logger.info("  - Worker Manager ready")
    
    async def _init_openclaw(self):
        """Initialize OpenClaw integration"""
        logger.info("Initializing OpenClaw integration...")
        
        # OpenClaw Client
        openclaw_config = OpenClawConfig(
            base_url=self.settings.openclaw_base_url,
            api_key=self.settings.openclaw_api_key,
        )
        self.openclaw_client = OpenClawClient(openclaw_config)
        logger.info("  - OpenClaw Client ready")
        
        # Web Scraper
        self.web_scraper = WebScraper()
        logger.info("  - Web Scraper ready")
        
        # Content Poster
        self.content_poster = ContentPoster()
        logger.info("  - Content Poster ready")
        
        # Automation Engine
        self.automation_engine = AutomationEngine()
        logger.info("  - Automation Engine ready")
    
    async def start(self):
        """Start the system"""
        if self._running:
            logger.warning("System is already running")
            return
        
        logger.info("Starting Emy-FullStack AI Developer System...")
        self._running = True
        self._start_time = datetime.utcnow()
        
        # Start Master Brain
        if self.master_brain:
            await self.master_brain.start()
        
        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._optimization_loop()),
            asyncio.create_task(self._feedback_collection_loop()),
            asyncio.create_task(self._health_check_loop()),
        ]
        
        logger.info("System started successfully!")
        logger.info(f"Environment: {self.settings.environment.value}")
        logger.info(f"Debug mode: {self.settings.debug}")
        logger.info(f"Active agents: {len(self.agents)}")
    
    async def stop(self):
        """Stop the system"""
        if not self._running:
            return
        
        logger.info("Stopping Emy-FullStack AI Developer System...")
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Stop Master Brain
        if self.master_brain:
            await self.master_brain.stop()
        
        # Close OpenClaw connections
        if self.openclaw_client:
            await self.openclaw_client.close()
        if self.web_scraper:
            await self.web_scraper.close()
        
        logger.info("System stopped")
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while self._running:
            try:
                if self.master_brain:
                    await self.master_brain.run_optimization_cycle()
            except Exception as e:
                logger.error(f"Optimization error: {e}")
            
            await asyncio.sleep(self.settings.optimization_interval)
    
    async def _feedback_collection_loop(self):
        """Background feedback collection loop"""
        while self._running:
            try:
                if self.feedback_loop:
                    # Collect metrics from all agents
                    for agent_type, agent in self.agents.items():
                        if hasattr(agent, 'get_metrics'):
                            metrics = agent.get_metrics()
                            self.feedback_loop.record_metrics(agent.agent_id, metrics)
            except Exception as e:
                logger.error(f"Feedback collection error: {e}")
            
            await asyncio.sleep(self.settings.feedback_collection_interval)
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            try:
                health = await self.get_health()
                if not health['healthy']:
                    logger.warning(f"System health degraded: {health}")
            except Exception as e:
                logger.error(f"Health check error: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def execute_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 5,
    ) -> Dict[str, Any]:
        """Execute a task through the system"""
        if not self._running:
            raise RuntimeError("System is not running")
        
        # Route task to appropriate agent
        agent_type = self.task_router.route(task_type)
        agent = self.agents.get(agent_type)
        
        if not agent:
            raise ValueError(f"No agent available for task type: {task_type}")
        
        # Add to priority queue if high priority
        if priority >= 7:
            await self.priority_queue.enqueue(
                task_id=task_data.get('task_id', f"task_{datetime.utcnow().timestamp()}"),
                task_type=task_type,
                priority=priority,
                data=task_data,
            )
        
        # Execute through agent
        result = await agent.execute(task_data)
        
        # Record in feedback loop
        if self.feedback_loop:
            self.feedback_loop.record_task_result(
                agent_id=agent.agent_id,
                task_type=task_type,
                success=result.get('success', False),
                duration=result.get('duration', 0),
            )
        
        return result
    
    async def create_project(
        self,
        project_name: str,
        project_type: str,
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new project using all agents"""
        logger.info(f"Creating project: {project_name}")
        
        # Have Project Manager create the plan
        pm_agent = self.agents.get(AgentType.PROJECT_MANAGER)
        if pm_agent:
            plan = await pm_agent.create_project_plan(
                project_name=project_name,
                project_type=project_type,
                requirements=requirements,
            )
        
        # Execute through coordinator
        if self.coordinator:
            workflow_id = await self.coordinator.create_workflow(
                name=f"project_{project_name}",
                steps=[
                    {'agent': AgentType.UIUX.value, 'action': 'design_wireframes'},
                    {'agent': AgentType.DATABASE.value, 'action': 'design_schema'},
                    {'agent': AgentType.BACKEND.value, 'action': 'create_api'},
                    {'agent': AgentType.FRONTEND.value, 'action': 'generate_ui'},
                    {'agent': AgentType.SECURITY.value, 'action': 'security_audit'},
                    {'agent': AgentType.QA.value, 'action': 'run_tests'},
                    {'agent': AgentType.DEVOPS.value, 'action': 'prepare_deployment'},
                ],
            )
            
            result = await self.coordinator.execute_workflow(workflow_id)
            return result
        
        return {'status': 'project_created', 'name': project_name}
    
    async def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        agent_health = {}
        
        for agent_type, agent in self.agents.items():
            if hasattr(agent, 'health_check'):
                agent_health[agent_type.value] = await agent.health_check()
            else:
                agent_health[agent_type.value] = {'status': 'unknown'}
        
        master_brain_health = 'healthy' if self.master_brain else 'not_initialized'
        
        all_healthy = all(
            h.get('status') != 'unhealthy'
            for h in agent_health.values()
        )
        
        return {
            'healthy': all_healthy and master_brain_health == 'healthy',
            'uptime_seconds': (datetime.utcnow() - self._start_time).total_seconds() if self._start_time else 0,
            'agents': agent_health,
            'master_brain': master_brain_health,
            'running': self._running,
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        return {
            'status': 'running' if self._running else 'stopped',
            'environment': self.settings.environment.value,
            'start_time': self._start_time.isoformat() if self._start_time else None,
            'agents_count': len(self.agents),
            'agents': [
                {
                    'type': agent_type.value,
                    'id': agent.agent_id,
                    'name': agent.name,
                }
                for agent_type, agent in self.agents.items()
            ],
            'master_brain': {
                'state': self.master_brain.state.value if self.master_brain else 'not_initialized',
            },
            'task_queue': {
                'router': 'active' if self.task_router else 'inactive',
                'priority_queue': 'active' if self.priority_queue else 'inactive',
            },
            'integrations': {
                'openclaw': 'connected' if self.openclaw_client else 'disconnected',
            },
        }


# Global system instance
_system: Optional[EmyFullStackSystem] = None


def get_system() -> EmyFullStackSystem:
    """Get or create the global system instance"""
    global _system
    if _system is None:
        _system = EmyFullStackSystem()
    return _system


async def main():
    """Main entry point"""
    system = get_system()
    
    # Handle signals for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(system.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Initialize and start system
        await system.initialize()
        await system.start()
        
        # Keep running
        while system._running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
