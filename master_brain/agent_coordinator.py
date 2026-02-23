"""
Agent Coordinator
Coordinates communication and collaboration between agents
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Set
from enum import Enum
from datetime import datetime, timedelta
import threading
import asyncio
import json
import uuid
from collections import defaultdict


class AgentState(Enum):
    """Agent operational states"""
    OFFLINE = "offline"
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class AgentInfo:
    """Information about a registered agent"""
    agent_id: str
    agent_type: str
    state: AgentState = AgentState.OFFLINE
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    task_count: int = 0
    error_count: int = 0
    last_heartbeat: Optional[datetime] = None
    registered_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'state': self.state.value,
            'capabilities': self.capabilities,
            'current_task': self.current_task,
            'task_count': self.task_count,
            'error_count': self.error_count,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'registered_at': self.registered_at.isoformat(),
            'metadata': self.metadata,
        }


@dataclass
class Message:
    """Inter-agent message"""
    message_id: str
    sender_id: str
    recipient_id: str  # Can be specific agent_id or agent_type or 'broadcast'
    message_type: str  # request, response, notification, event
    content: Dict[str, Any]
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[int] = None  # Time to live in seconds
    priority: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_type': self.message_type,
            'content': self.content,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat(),
            'ttl': self.ttl,
            'priority': self.priority,
        }


class AgentCoordinator:
    """
    Coordinates communication and task allocation between agents
    """
    
    AGENT_TYPES = [
        'frontend', 'backend', 'database', 'devops', 'qa',
        'uiux', 'security', 'aiml', 'project_manager'
    ]
    
    def __init__(self):
        # Agent registry
        self._agents: Dict[str, AgentInfo] = {}
        self._agents_by_type: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Message queues
        self._message_queues: Dict[str, List[Message]] = defaultdict(list)
        self._pending_responses: Dict[str, Dict[str, Any]] = {}
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Coordination state
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        # Health monitoring
        self._heartbeat_timeout = timedelta(seconds=60)
        self._monitoring = False
    
    # ========== Agent Registration ==========
    
    def register_agent(
        self,
        agent_type: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Register a new agent"""
        agent_id = f"{agent_type}-{uuid.uuid4().hex[:8]}"
        
        agent = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            state=AgentState.STARTING,
            capabilities=capabilities or [],
            metadata=metadata or {},
        )
        
        with self._lock:
            self._agents[agent_id] = agent
            self._agents_by_type[agent_type].append(agent_id)
        
        self._emit_event('agent_registered', {'agent_id': agent_id, 'agent_type': agent_type})
        
        return agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            agent = self._agents[agent_id]
            agent.state = AgentState.STOPPING
            
            # Remove from type index
            if agent_id in self._agents_by_type[agent.agent_type]:
                self._agents_by_type[agent.agent_type].remove(agent_id)
            
            # Clear message queue
            if agent_id in self._message_queues:
                del self._message_queues[agent_id]
            
            del self._agents[agent_id]
        
        self._emit_event('agent_unregistered', {'agent_id': agent_id})
        return True
    
    def update_agent_state(self, agent_id: str, state: AgentState):
        """Update agent state"""
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].state = state
                self._emit_event('agent_state_changed', {
                    'agent_id': agent_id,
                    'new_state': state.value,
                })
    
    def heartbeat(self, agent_id: str):
        """Record agent heartbeat"""
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].last_heartbeat = datetime.utcnow()
                if self._agents[agent_id].state == AgentState.STARTING:
                    self._agents[agent_id].state = AgentState.READY
    
    # ========== Messaging ==========
    
    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None,
        ttl: Optional[int] = None,
        priority: int = 5,
    ) -> str:
        """Send a message to another agent"""
        message = Message(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            correlation_id=correlation_id,
            ttl=ttl,
            priority=priority,
        )
        
        # Route message
        if recipient_id == 'broadcast':
            self._broadcast_message(message)
        elif recipient_id in self.AGENT_TYPES:
            self._send_to_type(message, recipient_id)
        else:
            self._deliver_message(message, recipient_id)
        
        return message.message_id
    
    def _deliver_message(self, message: Message, agent_id: str):
        """Deliver message to a specific agent"""
        with self._lock:
            self._message_queues[agent_id].append(message)
            # Sort by priority (higher first)
            self._message_queues[agent_id].sort(key=lambda m: m.priority, reverse=True)
    
    def _broadcast_message(self, message: Message):
        """Broadcast message to all agents"""
        with self._lock:
            for agent_id in self._agents.keys():
                if agent_id != message.sender_id:
                    msg_copy = Message(
                        message_id=f"{message.message_id}-{agent_id}",
                        sender_id=message.sender_id,
                        recipient_id=agent_id,
                        message_type=message.message_type,
                        content=message.content,
                        correlation_id=message.correlation_id,
                        ttl=message.ttl,
                        priority=message.priority,
                    )
                    self._message_queues[agent_id].append(msg_copy)
    
    def _send_to_type(self, message: Message, agent_type: str):
        """Send message to all agents of a type"""
        with self._lock:
            agent_ids = self._agents_by_type.get(agent_type, [])
            for agent_id in agent_ids:
                if agent_id != message.sender_id:
                    msg_copy = Message(
                        message_id=f"{message.message_id}-{agent_id}",
                        sender_id=message.sender_id,
                        recipient_id=agent_id,
                        message_type=message.message_type,
                        content=message.content,
                        correlation_id=message.correlation_id,
                        ttl=message.ttl,
                        priority=message.priority,
                    )
                    self._message_queues[agent_id].append(msg_copy)
    
    def get_messages(
        self,
        agent_id: str,
        limit: int = 10,
        message_type: Optional[str] = None,
    ) -> List[Message]:
        """Get pending messages for an agent"""
        with self._lock:
            messages = self._message_queues.get(agent_id, [])
            
            # Filter expired messages
            now = datetime.utcnow()
            messages = [
                m for m in messages
                if not m.ttl or (now - m.timestamp).total_seconds() < m.ttl
            ]
            
            if message_type:
                messages = [m for m in messages if m.message_type == message_type]
            
            # Get up to limit messages
            result = messages[:limit]
            
            # Remove returned messages from queue
            self._message_queues[agent_id] = messages[limit:]
            
            return result
    
    def request_response(
        self,
        sender_id: str,
        recipient_id: str,
        content: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response"""
        correlation_id = str(uuid.uuid4())
        
        # Create response placeholder
        self._pending_responses[correlation_id] = {
            'received': False,
            'response': None,
            'event': threading.Event(),
        }
        
        # Send request
        self.send_message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type='request',
            content=content,
            correlation_id=correlation_id,
        )
        
        # Wait for response
        event = self._pending_responses[correlation_id]['event']
        if event.wait(timeout):
            response = self._pending_responses[correlation_id]['response']
            del self._pending_responses[correlation_id]
            return response
        
        del self._pending_responses[correlation_id]
        return None
    
    def send_response(
        self,
        agent_id: str,
        correlation_id: str,
        content: Dict[str, Any],
    ):
        """Send a response to a request"""
        if correlation_id in self._pending_responses:
            self._pending_responses[correlation_id]['response'] = content
            self._pending_responses[correlation_id]['received'] = True
            self._pending_responses[correlation_id]['event'].set()
    
    # ========== Task Coordination ==========
    
    def assign_task(
        self,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any],
        preferred_agent: Optional[str] = None,
    ) -> Optional[str]:
        """Assign a task to an appropriate agent"""
        agent_id = preferred_agent
        
        if not agent_id:
            # Find best available agent
            agent_id = self._find_best_agent(task_type)
        
        if not agent_id:
            return None
        
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.current_task = task_id
                agent.state = AgentState.BUSY
                self._task_assignments[task_id] = agent_id
        
        # Send task to agent
        self.send_message(
            sender_id='coordinator',
            recipient_id=agent_id,
            message_type='task_assignment',
            content={
                'task_id': task_id,
                'task_type': task_type,
                'task_data': task_data,
            },
            priority=task_data.get('priority', 5),
        )
        
        return agent_id
    
    def _find_best_agent(self, task_type: str) -> Optional[str]:
        """Find the best available agent for a task type"""
        agent_type = self._map_task_to_agent_type(task_type)
        
        with self._lock:
            candidates = self._agents_by_type.get(agent_type, [])
            
            # Filter to ready agents
            ready_agents = [
                agent_id for agent_id in candidates
                if self._agents.get(agent_id, AgentInfo('', '')).state == AgentState.READY
            ]
            
            if not ready_agents:
                # Try busy agents (will queue)
                ready_agents = [
                    agent_id for agent_id in candidates
                    if self._agents.get(agent_id, AgentInfo('', '')).state == AgentState.BUSY
                ]
            
            if not ready_agents:
                return None
            
            # Select agent with lowest task count
            return min(ready_agents, key=lambda a: self._agents[a].task_count)
    
    def _map_task_to_agent_type(self, task_type: str) -> str:
        """Map task type to agent type"""
        mappings = {
            'frontend': ['flutter', 'widget', 'ui', 'screen', 'layout'],
            'backend': ['api', 'endpoint', 'crud', 'auth', 'middleware'],
            'database': ['database', 'schema', 'migration', 'query', 'cache'],
            'devops': ['docker', 'kubernetes', 'deploy', 'ci', 'cd'],
            'qa': ['test', 'qa', 'quality', 'coverage'],
            'uiux': ['design', 'wireframe', 'mockup', 'ux'],
            'security': ['security', 'encrypt', 'vulnerability', 'audit'],
            'aiml': ['ml', 'ai', 'model', 'predict', 'optimize'],
            'project_manager': ['project', 'task', 'milestone', 'sprint'],
        }
        
        task_lower = task_type.lower()
        
        for agent_type, keywords in mappings.items():
            if any(keyword in task_lower for keyword in keywords):
                return agent_type
        
        return 'backend'  # Default
    
    def complete_task(
        self,
        agent_id: str,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ):
        """Mark a task as complete"""
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.current_task = None
                agent.state = AgentState.READY
                agent.task_count += 1
                
                if not success:
                    agent.error_count += 1
            
            if task_id in self._task_assignments:
                del self._task_assignments[task_id]
        
        self._emit_event('task_completed', {
            'agent_id': agent_id,
            'task_id': task_id,
            'success': success,
            'result': result,
        })
    
    # ========== Workflow Coordination ==========
    
    def start_workflow(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a multi-agent workflow"""
        workflow_id = str(uuid.uuid4())
        
        self._active_workflows[workflow_id] = {
            'name': workflow_name,
            'steps': steps,
            'context': context or {},
            'current_step': 0,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'results': [],
        }
        
        # Start first step
        self._execute_workflow_step(workflow_id)
        
        return workflow_id
    
    def _execute_workflow_step(self, workflow_id: str):
        """Execute the current step of a workflow"""
        workflow = self._active_workflows.get(workflow_id)
        
        if not workflow or workflow['status'] != 'running':
            return
        
        current_step = workflow['current_step']
        
        if current_step >= len(workflow['steps']):
            workflow['status'] = 'completed'
            workflow['completed_at'] = datetime.utcnow()
            self._emit_event('workflow_completed', {'workflow_id': workflow_id})
            return
        
        step = workflow['steps'][current_step]
        
        # Assign task for this step
        task_id = str(uuid.uuid4())
        task_data = {
            'workflow_id': workflow_id,
            'step_index': current_step,
            'step_config': step,
            'context': workflow['context'],
            'priority': step.get('priority', 5),
        }
        
        self.assign_task(
            task_id=task_id,
            task_type=step.get('type', 'generic'),
            task_data=task_data,
        )
    
    def advance_workflow(
        self,
        workflow_id: str,
        step_result: Dict[str, Any],
    ):
        """Advance workflow to the next step"""
        workflow = self._active_workflows.get(workflow_id)
        
        if not workflow or workflow['status'] != 'running':
            return
        
        # Store result
        workflow['results'].append(step_result)
        
        # Update context with result
        workflow['context'].update(step_result.get('output', {}))
        
        # Advance to next step
        workflow['current_step'] += 1
        
        # Execute next step
        self._execute_workflow_step(workflow_id)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        workflow = self._active_workflows.get(workflow_id)
        
        if not workflow:
            return None
        
        return {
            'workflow_id': workflow_id,
            'name': workflow['name'],
            'status': workflow['status'],
            'current_step': workflow['current_step'],
            'total_steps': len(workflow['steps']),
            'started_at': workflow['started_at'].isoformat(),
            'completed_at': workflow.get('completed_at', '').isoformat() if workflow.get('completed_at') else None,
        }
    
    # ========== Events ==========
    
    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self._event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to handlers"""
        handlers = self._event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Event handler error for {event_type}: {e}")
    
    # ========== Monitoring ==========
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent"""
        agent = self._agents.get(agent_id)
        return agent.to_dict() if agent else None
    
    def get_all_agents(
        self,
        agent_type: Optional[str] = None,
        state: Optional[AgentState] = None,
    ) -> List[Dict[str, Any]]:
        """Get all agents with optional filtering"""
        agents = list(self._agents.values())
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        if state:
            agents = [a for a in agents if a.state == state]
        
        return [a.to_dict() for a in agents]
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics"""
        return {
            'total_agents': len(self._agents),
            'agents_by_type': {t: len(ids) for t, ids in self._agents_by_type.items()},
            'agents_by_state': {
                state.value: sum(1 for a in self._agents.values() if a.state == state)
                for state in AgentState
            },
            'active_workflows': len([w for w in self._active_workflows.values() if w['status'] == 'running']),
            'pending_tasks': len(self._task_assignments),
            'total_messages_queued': sum(len(q) for q in self._message_queues.values()),
        }
    
    def start_health_monitoring(self, interval: float = 30.0):
        """Start health monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                self._check_agent_health()
                threading.Event().wait(interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_health_monitoring(self):
        """Stop health monitoring"""
        self._monitoring = False
    
    def _check_agent_health(self):
        """Check health of all agents"""
        now = datetime.utcnow()
        
        with self._lock:
            for agent_id, agent in self._agents.items():
                if agent.last_heartbeat:
                    since_heartbeat = now - agent.last_heartbeat
                    
                    if since_heartbeat > self._heartbeat_timeout:
                        if agent.state not in [AgentState.OFFLINE, AgentState.ERROR]:
                            agent.state = AgentState.ERROR
                            self._emit_event('agent_unhealthy', {
                                'agent_id': agent_id,
                                'reason': 'heartbeat_timeout',
                                'last_heartbeat': agent.last_heartbeat.isoformat(),
                            })
