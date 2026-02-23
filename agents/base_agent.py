"""
Base Agent Framework for Emy-FullStack AI Developer System
All specialized agents inherit from this base class.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class AgentLog:
    """Log entry for agent activities."""
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: str = ""
    level: str = "INFO"
    message: str = ""
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "level": self.level,
            "message": self.message,
            "task_id": self.task_id,
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Emy-FullStack system.
    
    Provides:
    - Task processing capabilities
    - Logging infrastructure
    - Communication hooks for task queue
    - Lifecycle management
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        capabilities: List[str] = None,
        config: Dict[str, Any] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.config = config or {}
        self.is_running = False
        self.current_task: Optional[Task] = None
        self.task_history: List[Task] = []
        self.logs: List[AgentLog] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_fail": [],
            "on_log": [],
        }
        
        # Setup logging
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.logger.setLevel(logging.DEBUG)

    def log(self, message: str, level: str = "INFO", task_id: str = None, metadata: Dict = None):
        """Log an activity with optional task association."""
        log_entry = AgentLog(
            agent_name=self.name,
            level=level,
            message=message,
            task_id=task_id,
            metadata=metadata or {}
        )
        self.logs.append(log_entry)
        
        # Use Python logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{self.name}] {message}")
        
        # Trigger callbacks
        self._trigger_callback("on_log", log_entry)

    def register_callback(self, event: str, callback: Callable):
        """Register a callback for specific events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _trigger_callback(self, event: str, *args, **kwargs):
        """Trigger all callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

    async def receive_task(self, task: Task) -> Task:
        """
        Receive and process a task.
        
        Args:
            task: The task to execute
            
        Returns:
            The completed task with results
        """
        self.current_task = task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        task.assigned_to = self.name
        
        self.log(f"Received task: {task.name}", task_id=task.id)
        self._trigger_callback("on_task_start", task)
        
        try:
            # Execute the task
            result = await self.execute_task(task)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            self.log(f"Completed task: {task.name}", level="INFO", task_id=task.id)
            self._trigger_callback("on_task_complete", task)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.log(f"Failed task: {task.name} - {e}", level="ERROR", task_id=task.id)
            self._trigger_callback("on_task_fail", task, e)
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                self.log(f"Retrying task: {task.name} (attempt {task.retry_count})", task_id=task.id)
                return await self.receive_task(task)
        
        finally:
            self.task_history.append(task)
            self.current_task = None
        
        return task

    @abstractmethod
    async def execute_task(self, task: Task) -> Any:
        """
        Execute the given task. Must be implemented by subclasses.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of task execution
        """
        pass

    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task type."""
        task_type = task.metadata.get("type", "")
        return task_type in self.capabilities or not self.capabilities

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "id": self.id,
            "name": self.name,
            "is_running": self.is_running,
            "current_task": self.current_task.to_dict() if self.current_task else None,
            "tasks_completed": len([t for t in self.task_history if t.status == TaskStatus.COMPLETED]),
            "tasks_failed": len([t for t in self.task_history if t.status == TaskStatus.FAILED]),
            "capabilities": self.capabilities,
        }

    async def start(self):
        """Start the agent."""
        self.is_running = True
        self.log(f"Agent started")

    async def stop(self):
        """Stop the agent."""
        self.is_running = False
        self.log(f"Agent stopped")

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class AgentCommunicator:
    """
    Handles inter-agent communication.
    Agents can send messages to each other through this communicator.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> [agent_names]
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent for communication."""
        self.agents[agent.name] = agent
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        if agent_name in self.agents:
            del self.agents[agent_name]
    
    def subscribe(self, agent_name: str, topic: str):
        """Subscribe an agent to a topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        if agent_name not in self.subscriptions[topic]:
            self.subscriptions[topic].append(agent_name)
    
    async def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]):
        """Send a direct message to another agent."""
        await self.message_queue.put({
            "type": "direct",
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast(self, from_agent: str, topic: str, message: Dict[str, Any]):
        """Broadcast a message to all subscribers of a topic."""
        subscribers = self.subscriptions.get(topic, [])
        for subscriber in subscribers:
            await self.send_message(from_agent, subscriber, {
                "topic": topic,
                **message
            })
    
    async def get_message(self) -> Optional[Dict[str, Any]]:
        """Get the next message from the queue."""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None
