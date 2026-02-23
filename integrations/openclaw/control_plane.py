"""
OpenClaw Control Plane
External API gateway that controls the Emy-FullStack agent system
Receives commands from outside (webhooks, API calls) and delegates to Master Brain
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openclaw.control_plane")


# ============================================================================
# MODELS
# ============================================================================

class CommandType(str, Enum):
    """Types of commands OpenClaw can receive"""
    # Project commands
    CREATE_PROJECT = "create_project"
    BUILD_APP = "build_app"
    DEPLOY_APP = "deploy_app"
    
    # Agent commands
    RUN_AGENT = "run_agent"
    STOP_AGENT = "stop_agent"
    GET_AGENT_STATUS = "get_agent_status"
    
    # Task commands
    SUBMIT_TASK = "submit_task"
    CANCEL_TASK = "cancel_task"
    GET_TASK_STATUS = "get_task_status"
    
    # Code generation
    GENERATE_CODE = "generate_code"
    GENERATE_COMPONENT = "generate_component"
    
    # System commands
    SYSTEM_STATUS = "system_status"
    HEALTH_CHECK = "health_check"
    OPTIMIZE = "optimize"
    
    # Webhook triggers
    GITHUB_WEBHOOK = "github_webhook"
    CUSTOM_WEBHOOK = "custom_webhook"


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class ProjectType(str, Enum):
    """Project types that can be created"""
    FLUTTER_MOBILE = "flutter_mobile"
    FLUTTER_WEB = "flutter_web"
    FLUTTER_FULL = "flutter_full"
    FASTAPI_BACKEND = "fastapi_backend"
    FULLSTACK = "fullstack"


class CommandRequest(BaseModel):
    """Request to execute a command"""
    command: CommandType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    callback_url: Optional[str] = None  # Webhook to call when complete
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateProjectRequest(BaseModel):
    """Request to create a new project"""
    name: str
    project_type: ProjectType
    description: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    database: str = "postgresql"
    auth_enabled: bool = True
    output_path: Optional[str] = None


class GenerateCodeRequest(BaseModel):
    """Request to generate code"""
    generation_type: str  # flutter_widget, api_endpoint, etc.
    description: str
    language: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)


class TaskSubmission(BaseModel):
    """Submit a task for agents to process"""
    task_type: str
    description: str
    target_agent: Optional[str] = None  # If None, Master Brain decides
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)


class WebhookPayload(BaseModel):
    """Generic webhook payload"""
    event_type: str
    source: str
    data: Dict[str, Any]
    signature: Optional[str] = None


class CommandResponse(BaseModel):
    """Response from command execution"""
    command_id: str
    status: str  # queued, processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================================
# CONTROL PLANE
# ============================================================================

class OpenClawControlPlane:
    """
    Central control plane for the agent system
    Receives external commands and coordinates with Master Brain
    """
    
    def __init__(self):
        self._commands: Dict[str, CommandResponse] = {}
        self._master_brain = None
        self._task_queue = None
        self._project_creator = None
        self._ai_generator = None
        self._agents: Dict[str, Any] = {}
        self._initialized = False
        
    async def initialize(self):
        """Initialize connections to internal systems"""
        if self._initialized:
            return
            
        logger.info("Initializing OpenClaw Control Plane...")
        
        # Import and initialize Master Brain
        try:
            from master_brain import MasterBrain
            self._master_brain = MasterBrain()
            await self._master_brain.start()
            logger.info("✅ Master Brain connected")
        except Exception as e:
            logger.warning(f"⚠️ Master Brain not available: {e}")
        
        # Import and initialize Task Queue
        try:
            from task_queue import TaskQueue, TaskRouter
            self._task_queue = TaskQueue()
            self._task_router = TaskRouter()
            logger.info("✅ Task Queue connected")
        except Exception as e:
            logger.warning(f"⚠️ Task Queue not available: {e}")
        
        # Import Project Creator
        try:
            from core import ProjectCreator, AICodeGenerator
            self._project_creator = ProjectCreator()
            self._ai_generator = AICodeGenerator()
            logger.info("✅ Project Creator connected")
        except Exception as e:
            logger.warning(f"⚠️ Project Creator not available: {e}")
        
        # Import Agents
        try:
            from agents import (
                FrontendAgent, BackendAgent, DatabaseAgent,
                DevOpsAgent, QAAgent, UIUXAgent,
                SecurityAgent, AIMLAgent, ProjectManagerAgent
            )
            self._agents = {
                'frontend': FrontendAgent(),
                'backend': BackendAgent(),
                'database': DatabaseAgent(),
                'devops': DevOpsAgent(),
                'qa': QAAgent(),
                'uiux': UIUXAgent(),
                'security': SecurityAgent(),
                'aiml': AIMLAgent(),
                'project_manager': ProjectManagerAgent(),
            }
            logger.info(f"✅ {len(self._agents)} Agents connected")
        except Exception as e:
            logger.warning(f"⚠️ Agents not fully available: {e}")
        
        self._initialized = True
        logger.info("OpenClaw Control Plane initialized")
    
    async def execute_command(
        self, 
        command: CommandType, 
        parameters: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        callback_url: Optional[str] = None
    ) -> CommandResponse:
        """Execute a command and return response"""
        command_id = str(uuid.uuid4())
        response = CommandResponse(
            command_id=command_id,
            status="processing",
            started_at=datetime.utcnow()
        )
        self._commands[command_id] = response
        
        try:
            if command == CommandType.CREATE_PROJECT:
                result = await self._create_project(parameters)
            elif command == CommandType.BUILD_APP:
                result = await self._build_app(parameters)
            elif command == CommandType.DEPLOY_APP:
                result = await self._deploy_app(parameters)
            elif command == CommandType.RUN_AGENT:
                result = await self._run_agent(parameters)
            elif command == CommandType.SUBMIT_TASK:
                result = await self._submit_task(parameters, priority)
            elif command == CommandType.GENERATE_CODE:
                result = await self._generate_code(parameters)
            elif command == CommandType.SYSTEM_STATUS:
                result = await self._get_system_status()
            elif command == CommandType.HEALTH_CHECK:
                result = await self._health_check()
            elif command == CommandType.OPTIMIZE:
                result = await self._optimize_system()
            elif command == CommandType.GITHUB_WEBHOOK:
                result = await self._handle_github_webhook(parameters)
            elif command == CommandType.CUSTOM_WEBHOOK:
                result = await self._handle_custom_webhook(parameters)
            else:
                result = {"message": f"Command {command} acknowledged"}
            
            response.status = "completed"
            response.result = result
            response.completed_at = datetime.utcnow()
            
            # Call callback if provided
            if callback_url:
                await self._send_callback(callback_url, response)
                
        except Exception as e:
            logger.error(f"Command {command} failed: {e}")
            response.status = "failed"
            response.error = str(e)
            response.completed_at = datetime.utcnow()
        
        self._commands[command_id] = response
        return response
    
    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================
    
    async def _create_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project via Master Brain"""
        logger.info(f"Creating project: {params.get('name')}")
        
        if self._project_creator:
            from core import ProjectConfig
            config = ProjectConfig(
                name=params.get('name', 'NewProject'),
                project_type=params.get('project_type', 'fullstack'),
                database=params.get('database', 'postgresql'),
                auth_enabled=params.get('auth_enabled', True),
                features=params.get('features', []),
            )
            output_path = params.get('output_path', f"./{config.name.lower()}")
            result = self._project_creator.create_project(config, output_path)
            
            # Notify Master Brain
            if self._master_brain:
                await self._notify_master_brain("project_created", {
                    "name": config.name,
                    "path": output_path,
                    "type": config.project_type,
                })
            
            return result
        else:
            raise HTTPException(status_code=503, detail="Project Creator not available")
    
    async def _build_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build application using agents"""
        logger.info(f"Building app: {params}")
        
        # Delegate to Master Brain which coordinates agents
        if self._master_brain:
            task_id = await self._master_brain.submit_task({
                'type': 'build_application',
                'parameters': params,
                'agents_involved': ['frontend', 'backend', 'database', 'devops'],
            })
            return {"task_id": task_id, "status": "building"}
        
        raise HTTPException(status_code=503, detail="Master Brain not available")
    
    async def _deploy_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application via DevOps agent"""
        logger.info(f"Deploying app: {params}")
        
        devops = self._agents.get('devops')
        if devops:
            from task_queue import Task, TaskPriority as TP
            task = Task(
                task_id=str(uuid.uuid4()),
                task_type="deployment",
                priority=TP.HIGH,
                payload=params,
            )
            result = await devops.process_task(task)
            return result
        
        raise HTTPException(status_code=503, detail="DevOps agent not available")
    
    async def _run_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific agent with a task"""
        agent_name = params.get('agent', '').lower()
        task_data = params.get('task', {})
        
        agent = self._agents.get(agent_name)
        if not agent:
            available = list(self._agents.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Agent '{agent_name}' not found. Available: {available}"
            )
        
        from task_queue import Task, TaskPriority as TP
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type=task_data.get('type', 'general'),
            priority=TP.MEDIUM,
            payload=task_data,
        )
        
        result = await agent.process_task(task)
        
        # Report to Master Brain
        if self._master_brain:
            await self._notify_master_brain("agent_task_completed", {
                "agent": agent_name,
                "task_id": task.task_id,
                "result": result,
            })
        
        return result
    
    async def _submit_task(self, params: Dict[str, Any], priority: TaskPriority) -> Dict[str, Any]:
        """Submit task to Master Brain for delegation"""
        if self._master_brain:
            task_id = await self._master_brain.submit_task({
                'type': params.get('task_type'),
                'description': params.get('description'),
                'parameters': params.get('parameters', {}),
                'target_agent': params.get('target_agent'),
                'priority': priority.value,
            })
            return {"task_id": task_id, "status": "queued"}
        
        raise HTTPException(status_code=503, detail="Master Brain not available")
    
    async def _generate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code using AI generator"""
        if self._ai_generator:
            from core import CodeGenerationRequest, GenerationType
            
            gen_type_str = params.get('generation_type', 'general')
            try:
                gen_type = GenerationType[gen_type_str.upper()]
            except KeyError:
                gen_type = GenerationType.GENERAL
            
            request = CodeGenerationRequest(
                generation_type=gen_type,
                description=params.get('description', ''),
                requirements=params.get('requirements', []),
            )
            
            result = await self._ai_generator.generate(request)
            return {
                "code": result.code,
                "filename": result.filename,
                "dependencies": result.dependencies,
            }
        
        raise HTTPException(status_code=503, detail="AI Generator not available")
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get full system status"""
        status = {
            "control_plane": "active",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {},
        }
        
        # Master Brain status
        if self._master_brain:
            status["components"]["master_brain"] = {
                "status": self._master_brain.state.value if hasattr(self._master_brain, 'state') else "active",
                "connected": True,
            }
        else:
            status["components"]["master_brain"] = {"status": "unavailable", "connected": False}
        
        # Agent statuses
        status["components"]["agents"] = {}
        for name, agent in self._agents.items():
            status["components"]["agents"][name] = {
                "status": "ready",
                "type": agent.agent_type if hasattr(agent, 'agent_type') else name,
            }
        
        # Task Queue status
        if self._task_queue:
            status["components"]["task_queue"] = {"status": "active", "connected": True}
        else:
            status["components"]["task_queue"] = {"status": "unavailable", "connected": False}
        
        return status
    
    async def _health_check(self) -> Dict[str, Any]:
        """Quick health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "master_brain": self._master_brain is not None,
            "agents_count": len(self._agents),
            "task_queue": self._task_queue is not None,
        }
    
    async def _optimize_system(self) -> Dict[str, Any]:
        """Trigger system optimization via Master Brain"""
        if self._master_brain and hasattr(self._master_brain, 'optimize'):
            result = await self._master_brain.optimize()
            return {"optimization": "completed", "result": result}
        
        return {"optimization": "skipped", "reason": "Master Brain optimizer not available"}
    
    async def _handle_github_webhook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub webhook events"""
        event_type = params.get('event_type', 'push')
        data = params.get('data', {})
        
        logger.info(f"GitHub webhook: {event_type}")
        
        # Determine action based on event
        if event_type == 'push':
            # Trigger CI/CD pipeline
            return await self._trigger_cicd(data)
        elif event_type == 'pull_request':
            # Trigger code review
            return await self._trigger_code_review(data)
        elif event_type == 'issues':
            # Create task from issue
            return await self._create_task_from_issue(data)
        
        return {"webhook": "received", "event": event_type}
    
    async def _handle_custom_webhook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom webhook events"""
        event_type = params.get('event_type', 'custom')
        data = params.get('data', {})
        
        logger.info(f"Custom webhook: {event_type}")
        
        # Route to appropriate handler based on event
        if self._master_brain:
            await self._notify_master_brain("webhook_received", {
                "event_type": event_type,
                "data": data,
            })
        
        return {"webhook": "processed", "event": event_type}
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _notify_master_brain(self, event_type: str, data: Dict[str, Any]):
        """Send notification to Master Brain"""
        if self._master_brain and hasattr(self._master_brain, 'receive_notification'):
            await self._master_brain.receive_notification(event_type, data)
    
    async def _send_callback(self, url: str, response: CommandResponse):
        """Send callback to external URL"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=response.dict()) as resp:
                    logger.info(f"Callback sent to {url}: {resp.status}")
        except Exception as e:
            logger.error(f"Callback failed: {e}")
    
    async def _trigger_cicd(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger CI/CD pipeline"""
        devops = self._agents.get('devops')
        if devops:
            from task_queue import Task, TaskPriority as TP
            task = Task(
                task_id=str(uuid.uuid4()),
                task_type="ci_cd_pipeline",
                priority=TP.HIGH,
                payload={"trigger": "github_push", "data": data},
            )
            result = await devops.process_task(task)
            return {"cicd": "triggered", "result": result}
        return {"cicd": "skipped", "reason": "DevOps agent not available"}
    
    async def _trigger_code_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger code review"""
        qa = self._agents.get('qa')
        if qa:
            from task_queue import Task, TaskPriority as TP
            task = Task(
                task_id=str(uuid.uuid4()),
                task_type="code_review",
                priority=TP.MEDIUM,
                payload={"trigger": "pull_request", "data": data},
            )
            result = await qa.process_task(task)
            return {"review": "triggered", "result": result}
        return {"review": "skipped", "reason": "QA agent not available"}
    
    async def _create_task_from_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task from GitHub issue"""
        pm = self._agents.get('project_manager')
        if pm:
            from task_queue import Task, TaskPriority as TP
            task = Task(
                task_id=str(uuid.uuid4()),
                task_type="create_task",
                priority=TP.MEDIUM,
                payload={"source": "github_issue", "data": data},
            )
            result = await pm.process_task(task)
            return {"task_created": True, "result": result}
        return {"task_created": False, "reason": "Project Manager agent not available"}
    
    def get_command_status(self, command_id: str) -> Optional[CommandResponse]:
        """Get status of a command"""
        return self._commands.get(command_id)


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Global control plane instance
control_plane = OpenClawControlPlane()

# API Key security
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    """Verify API key for authentication"""
    expected_key = os.getenv("OPENCLAW_API_KEY")
    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


# Create FastAPI app
app = FastAPI(
    title="OpenClaw Control Plane",
    description="External API gateway for Emy-FullStack AI Agent System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize control plane on startup"""
    await control_plane.initialize()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OpenClaw Control Plane",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return await control_plane._health_check()


@app.get("/status")
async def system_status(api_key: str = Depends(verify_api_key)):
    """Get full system status"""
    return await control_plane._get_system_status()


@app.post("/command", response_model=CommandResponse)
async def execute_command(
    request: CommandRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Execute a command on the agent system"""
    response = await control_plane.execute_command(
        command=request.command,
        parameters=request.parameters,
        priority=request.priority,
        callback_url=request.callback_url,
    )
    return response


@app.get("/command/{command_id}")
async def get_command_status(
    command_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get status of a command"""
    response = control_plane.get_command_status(command_id)
    if not response:
        raise HTTPException(status_code=404, detail="Command not found")
    return response


@app.post("/project/create")
async def create_project(
    request: CreateProjectRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new project"""
    response = await control_plane.execute_command(
        command=CommandType.CREATE_PROJECT,
        parameters=request.dict(),
    )
    return response


@app.post("/generate")
async def generate_code(
    request: GenerateCodeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate code using AI"""
    response = await control_plane.execute_command(
        command=CommandType.GENERATE_CODE,
        parameters=request.dict(),
    )
    return response


@app.post("/task")
async def submit_task(
    request: TaskSubmission,
    api_key: str = Depends(verify_api_key)
):
    """Submit a task to the agent system"""
    response = await control_plane.execute_command(
        command=CommandType.SUBMIT_TASK,
        parameters=request.dict(),
        priority=request.priority,
    )
    return response


@app.post("/agent/{agent_name}/run")
async def run_agent(
    agent_name: str,
    task: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Run a specific agent with a task"""
    response = await control_plane.execute_command(
        command=CommandType.RUN_AGENT,
        parameters={"agent": agent_name, "task": task},
    )
    return response


@app.get("/agents")
async def list_agents(api_key: str = Depends(verify_api_key)):
    """List all available agents"""
    agents = []
    for name, agent in control_plane._agents.items():
        agents.append({
            "name": name,
            "type": agent.agent_type if hasattr(agent, 'agent_type') else name,
            "description": agent.description if hasattr(agent, 'description') else "",
            "capabilities": agent.capabilities if hasattr(agent, 'capabilities') else [],
        })
    return {"agents": agents, "count": len(agents)}


@app.post("/deploy")
async def deploy_app(
    params: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """Deploy application"""
    response = await control_plane.execute_command(
        command=CommandType.DEPLOY_APP,
        parameters=params,
    )
    return response


@app.post("/webhook/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events"""
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "push")
    
    response = await control_plane.execute_command(
        command=CommandType.GITHUB_WEBHOOK,
        parameters={"event_type": event_type, "data": payload},
    )
    return response


@app.post("/webhook/custom")
async def custom_webhook(
    payload: WebhookPayload,
    api_key: str = Depends(verify_api_key)
):
    """Handle custom webhook events"""
    response = await control_plane.execute_command(
        command=CommandType.CUSTOM_WEBHOOK,
        parameters=payload.dict(),
    )
    return response


@app.post("/optimize")
async def optimize_system(api_key: str = Depends(verify_api_key)):
    """Trigger system optimization"""
    response = await control_plane.execute_command(
        command=CommandType.OPTIMIZE,
        parameters={},
    )
    return response


# ============================================================================
# CLI RUNNER
# ============================================================================

def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the control plane server"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
