"""
Master Brain
Central orchestration intelligence for the Emy-FullStack agent system
Receives logs from all agents, optimizes task assignments, implements feedback loops
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


class BrainState(Enum):
    """Master Brain operational states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    OPTIMIZING = "optimizing"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentMessage:
    """Message from an agent to Master Brain"""
    agent_id: str
    agent_type: str
    message_type: str  # log, metric, request, result, error
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: int = 5
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority,
            'correlation_id': self.correlation_id,
        }


@dataclass
class Decision:
    """A decision made by Master Brain"""
    decision_id: str
    decision_type: str  # task_assignment, priority_change, resource_allocation, optimization
    target_agents: List[str]
    parameters: Dict[str, Any]
    reasoning: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed: bool = False
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'decision_type': self.decision_type,
            'target_agents': self.target_agents,
            'parameters': self.parameters,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'executed': self.executed,
            'result': self.result,
        }


class MasterBrain:
    """
    Master Brain - Central Intelligence System
    
    Responsibilities:
    - Collect and analyze logs from all agents
    - Optimize task distribution and prioritization
    - Implement feedback loops for continuous improvement
    - Coordinate cross-agent operations
    - Monitor system health and performance
    """
    
    AGENT_TYPES = [
        'frontend', 'backend', 'database', 'devops', 'qa',
        'uiux', 'security', 'aiml', 'project_manager'
    ]
    
    def __init__(self):
        self.state = BrainState.INITIALIZING
        self.brain_id = str(uuid.uuid4())
        
        # Message handling
        self._message_queue: List[AgentMessage] = []
        self._message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Agent tracking
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._agent_metrics: Dict[str, Dict[str, Any]] = {}
        self._agent_last_seen: Dict[str, datetime] = {}
        
        # Decision history
        self._decisions: List[Decision] = []
        self._pending_decisions: List[Decision] = []
        
        # System metrics
        self._system_metrics: Dict[str, Any] = {
            'total_tasks_processed': 0,
            'total_decisions_made': 0,
            'optimization_cycles': 0,
            'start_time': datetime.utcnow(),
        }
        
        # Learning/optimization data
        self._performance_history: Dict[str, List[Dict]] = defaultdict(list)
        self._task_completion_times: Dict[str, List[float]] = defaultdict(list)
        self._error_patterns: Dict[str, int] = defaultdict(int)
        
        # Task tracking (for OpenClaw Control Plane)
        self._pending_tasks: Dict[str, Dict[str, Any]] = {}
        
        self.state = BrainState.ACTIVE
    
    # ========== Message Handling ==========
    
    def receive_message(self, message: AgentMessage):
        """Receive a message from an agent"""
        with self._lock:
            self._message_queue.append(message)
            self._update_agent_status(message)
        
        # Process message by type
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                self._log_error(f"Handler error for {message.message_type}: {e}")
        
        # Always analyze for insights
        self._analyze_message(message)
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a message type"""
        self._message_handlers[message_type].append(handler)
    
    def _update_agent_status(self, message: AgentMessage):
        """Update agent tracking based on message"""
        agent_id = message.agent_id
        self._agent_last_seen[agent_id] = message.timestamp
        
        if agent_id not in self._agent_registry:
            self._agent_registry[agent_id] = {
                'agent_type': message.agent_type,
                'first_seen': message.timestamp,
                'message_count': 0,
                'status': 'active',
            }
        
        self._agent_registry[agent_id]['message_count'] += 1
        self._agent_registry[agent_id]['last_message_type'] = message.message_type
    
    def _analyze_message(self, message: AgentMessage):
        """Analyze message for optimization insights"""
        content = message.content
        
        # Track task completions
        if message.message_type == 'result':
            if 'duration' in content:
                self._task_completion_times[message.agent_type].append(content['duration'])
            self._system_metrics['total_tasks_processed'] += 1
        
        # Track errors
        elif message.message_type == 'error':
            error_type = content.get('error_type', 'unknown')
            self._error_patterns[f"{message.agent_type}:{error_type}"] += 1
        
        # Track performance metrics
        elif message.message_type == 'metric':
            self._performance_history[message.agent_type].append({
                'timestamp': message.timestamp.isoformat(),
                'metrics': content,
            })
    
    # ========== Decision Making ==========
    
    def make_decision(
        self,
        decision_type: str,
        target_agents: List[str],
        parameters: Dict[str, Any],
        reasoning: str,
        confidence: float = 0.8,
    ) -> Decision:
        """Create a new decision"""
        decision = Decision(
            decision_id=str(uuid.uuid4()),
            decision_type=decision_type,
            target_agents=target_agents,
            parameters=parameters,
            reasoning=reasoning,
            confidence=confidence,
        )
        
        with self._lock:
            self._pending_decisions.append(decision)
        
        return decision
    
    def execute_decision(self, decision: Decision) -> bool:
        """Execute a pending decision"""
        try:
            # Route decision based on type
            if decision.decision_type == 'task_assignment':
                self._execute_task_assignment(decision)
            elif decision.decision_type == 'priority_change':
                self._execute_priority_change(decision)
            elif decision.decision_type == 'resource_allocation':
                self._execute_resource_allocation(decision)
            elif decision.decision_type == 'optimization':
                self._execute_optimization(decision)
            
            decision.executed = True
            decision.result = {'status': 'success'}
            
            with self._lock:
                self._decisions.append(decision)
                if decision in self._pending_decisions:
                    self._pending_decisions.remove(decision)
                self._system_metrics['total_decisions_made'] += 1
            
            return True
            
        except Exception as e:
            decision.result = {'status': 'failed', 'error': str(e)}
            self._log_error(f"Decision execution failed: {e}")
            return False
    
    def _execute_task_assignment(self, decision: Decision):
        """Execute a task assignment decision"""
        from task_queue import PriorityTaskQueue, TaskPriority
        
        queue = PriorityTaskQueue()
        
        for agent_id in decision.target_agents:
            task_params = decision.parameters.get('task', {})
            queue.enqueue(
                task_name=f"agents.{agent_id}.{task_params.get('action', 'execute')}",
                payload=task_params,
                priority=TaskPriority(task_params.get('priority', 5)),
            )
    
    def _execute_priority_change(self, decision: Decision):
        """Execute a priority change decision"""
        from task_queue import PriorityTaskQueue, TaskPriority
        
        queue = PriorityTaskQueue()
        
        task_id = decision.parameters.get('task_id')
        new_priority = TaskPriority(decision.parameters.get('new_priority', 5))
        
        if task_id:
            queue.update_priority(task_id, new_priority)
    
    def _execute_resource_allocation(self, decision: Decision):
        """Execute a resource allocation decision"""
        from task_queue import WorkerManager
        
        manager = WorkerManager()
        
        for agent_type in decision.target_agents:
            target_workers = decision.parameters.get('target_workers', {}).get(agent_type)
            if target_workers:
                manager.scale_pool(agent_type, target_workers)
    
    def _execute_optimization(self, decision: Decision):
        """Execute an optimization decision"""
        optimization_type = decision.parameters.get('optimization_type')
        
        if optimization_type == 'rebalance_queues':
            self._rebalance_queues(decision.parameters)
        elif optimization_type == 'adjust_concurrency':
            self._adjust_concurrency(decision.parameters)
    
    # ========== Optimization ==========
    
    def run_optimization_cycle(self):
        """Run a full optimization cycle"""
        self.state = BrainState.OPTIMIZING
        
        try:
            # Analyze current system state
            analysis = self._analyze_system_state()
            
            # Generate optimization decisions
            decisions = self._generate_optimization_decisions(analysis)
            
            # Execute high-confidence decisions automatically
            for decision in decisions:
                if decision.confidence >= 0.9:
                    self.execute_decision(decision)
                else:
                    # Queue for review
                    self._pending_decisions.append(decision)
            
            self._system_metrics['optimization_cycles'] += 1
            
        finally:
            self.state = BrainState.ACTIVE
    
    def _analyze_system_state(self) -> Dict[str, Any]:
        """Analyze current system state for optimization"""
        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'active_agents': len([a for a in self._agent_registry.values() if a['status'] == 'active']),
            'queue_depths': {},
            'agent_performance': {},
            'bottlenecks': [],
            'recommendations': [],
        }
        
        # Analyze agent performance
        for agent_type in self.AGENT_TYPES:
            times = self._task_completion_times.get(agent_type, [])
            if times:
                analysis['agent_performance'][agent_type] = {
                    'avg_completion_time': sum(times) / len(times),
                    'task_count': len(times),
                    'recent_trend': self._calculate_trend(times),
                }
        
        # Identify bottlenecks
        for agent_type, perf in analysis['agent_performance'].items():
            if perf.get('recent_trend') == 'increasing':
                analysis['bottlenecks'].append({
                    'agent_type': agent_type,
                    'issue': 'increasing_completion_time',
                    'severity': 'medium',
                })
        
        # Check for errors
        for error_key, count in self._error_patterns.items():
            if count > 10:
                agent_type, error_type = error_key.split(':')
                analysis['bottlenecks'].append({
                    'agent_type': agent_type,
                    'issue': f'frequent_errors:{error_type}',
                    'severity': 'high' if count > 50 else 'medium',
                    'count': count,
                })
        
        return analysis
    
    def _generate_optimization_decisions(self, analysis: Dict) -> List[Decision]:
        """Generate optimization decisions based on analysis"""
        decisions = []
        
        # Address bottlenecks
        for bottleneck in analysis.get('bottlenecks', []):
            agent_type = bottleneck['agent_type']
            issue = bottleneck['issue']
            
            if issue == 'increasing_completion_time':
                # Scale up workers
                decisions.append(self.make_decision(
                    decision_type='resource_allocation',
                    target_agents=[agent_type],
                    parameters={'increase_workers': 1},
                    reasoning=f"Increasing workers for {agent_type} due to slow completion times",
                    confidence=0.85,
                ))
            
            elif 'frequent_errors' in issue:
                # Reduce load, add monitoring
                decisions.append(self.make_decision(
                    decision_type='optimization',
                    target_agents=[agent_type],
                    parameters={
                        'optimization_type': 'reduce_load',
                        'rate_limit': '50/m',
                    },
                    reasoning=f"Reducing load on {agent_type} due to frequent errors",
                    confidence=0.9,
                ))
        
        return decisions
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from recent values"""
        if len(values) < 5:
            return 'stable'
        
        recent = values[-5:]
        older = values[-10:-5] if len(values) >= 10 else values[:5]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        if recent_avg > older_avg * 1.2:
            return 'increasing'
        elif recent_avg < older_avg * 0.8:
            return 'decreasing'
        return 'stable'
    
    def _rebalance_queues(self, parameters: Dict):
        """Rebalance work across queues"""
        pass  # Implementation depends on specific requirements
    
    def _adjust_concurrency(self, parameters: Dict):
        """Adjust worker concurrency"""
        pass  # Implementation depends on specific requirements
    
    # ========== Coordination ==========
    
    def coordinate_workflow(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Coordinate a multi-agent workflow"""
        workflow_id = str(uuid.uuid4())
        
        # Create task chain for workflow
        from task_queue import PriorityTaskQueue, TaskPriority
        
        queue = PriorityTaskQueue()
        previous_task_id = None
        
        for i, step in enumerate(steps):
            agent_type = step.get('agent')
            action = step.get('action')
            params = step.get('params', {})
            
            dependencies = []
            if previous_task_id:
                dependencies.append(previous_task_id)
            
            task_id = queue.enqueue(
                task_name=f"agents.{agent_type}.{action}",
                payload={
                    'workflow_id': workflow_id,
                    'step': i,
                    'context': context,
                    **params,
                },
                priority=TaskPriority(step.get('priority', 5)),
                dependencies=dependencies,
            )
            
            previous_task_id = task_id
        
        return workflow_id
    
    def broadcast_to_agents(
        self,
        agent_types: List[str],
        message_type: str,
        content: Dict[str, Any],
    ):
        """Broadcast a message to multiple agent types"""
        from task_queue import PriorityTaskQueue, TaskPriority
        
        queue = PriorityTaskQueue()
        
        for agent_type in agent_types:
            queue.enqueue(
                task_name=f"agents.{agent_type}.receive_broadcast",
                payload={
                    'message_type': message_type,
                    'content': content,
                    'from': 'master_brain',
                },
                priority=TaskPriority.HIGH,
            )
    
    # ========== Monitoring ==========
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'brain_id': self.brain_id,
            'state': self.state.value,
            'uptime_seconds': (datetime.utcnow() - self._system_metrics['start_time']).total_seconds(),
            'metrics': self._system_metrics,
            'active_agents': len([a for a in self._agent_registry.values() if a['status'] == 'active']),
            'pending_decisions': len(self._pending_decisions),
            'message_queue_size': len(self._message_queue),
        }
    
    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of agents"""
        if agent_id:
            return self._agent_registry.get(agent_id, {})
        return dict(self._agent_registry)
    
    def get_decision_history(
        self,
        limit: int = 50,
        decision_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision history"""
        decisions = self._decisions
        
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        return [d.to_dict() for d in decisions[-limit:]]
    
    def _log_error(self, message: str):
        """Log an error"""
        print(f"[MasterBrain Error] {datetime.utcnow().isoformat()}: {message}")
    
    # ========== OpenClaw Control Plane Integration ==========
    
    async def start(self):
        """Start the Master Brain (async for control plane)"""
        self.state = BrainState.ACTIVE
        # Start background optimization
        self._start_background_optimization()
        return {"status": "started", "brain_id": self.brain_id}
    
    async def submit_task(self, task_data: Dict[str, Any]) -> str:
        """
        Submit a task for processing.
        Called by OpenClaw Control Plane.
        Returns task_id for tracking.
        """
        task_id = str(uuid.uuid4())
        
        task_type = task_data.get('type', 'general')
        target_agent = task_data.get('target_agent')
        priority = task_data.get('priority', 'medium')
        
        # Determine which agent should handle this
        if not target_agent:
            target_agent = self._route_task(task_type)
        
        # Create decision for task assignment
        decision = self.make_decision(
            decision_type='task_assignment',
            target_agents=[target_agent] if target_agent else self.AGENT_TYPES,
            parameters={
                'task_id': task_id,
                'task_type': task_type,
                'task_data': task_data,
            },
            reasoning=f"Task {task_type} routed to {target_agent or 'auto'}",
            confidence=0.9 if target_agent else 0.7,
        )
        
        # Store task for tracking
        self._pending_tasks[task_id] = {
            'task_data': task_data,
            'decision': decision,
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
        }
        
        return task_id
    
    def _route_task(self, task_type: str) -> Optional[str]:
        """Route task to appropriate agent based on type"""
        routing_map = {
            # Frontend tasks
            'flutter': 'frontend',
            'widget': 'frontend',
            'ui': 'frontend',
            'screen': 'frontend',
            # Backend tasks  
            'api': 'backend',
            'endpoint': 'backend',
            'fastapi': 'backend',
            # Database tasks
            'database': 'database',
            'schema': 'database',
            'migration': 'database',
            'sql': 'database',
            # DevOps tasks
            'deploy': 'devops',
            'docker': 'devops',
            'ci': 'devops',
            'cd': 'devops',
            'kubernetes': 'devops',
            # QA tasks
            'test': 'qa',
            'quality': 'qa',
            # Security tasks
            'security': 'security',
            'auth': 'security',
            # AI/ML tasks
            'ai': 'aiml',
            'ml': 'aiml',
            'generate': 'aiml',
            # Project management
            'plan': 'project_manager',
            'sprint': 'project_manager',
            'task': 'project_manager',
        }
        
        task_lower = task_type.lower()
        for key, agent in routing_map.items():
            if key in task_lower:
                return agent
        
        return None  # Let Master Brain decide dynamically
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Run optimization cycle.
        Called by OpenClaw Control Plane.
        """
        self.state = BrainState.OPTIMIZING
        result = self.run_optimization_cycle()
        self.state = BrainState.ACTIVE
        return result
    
    async def receive_notification(self, event_type: str, data: Dict[str, Any]):
        """
        Receive notification from OpenClaw Control Plane.
        Process events like webhook triggers, task completions, etc.
        """
        message = AgentMessage(
            agent_id='openclaw_control_plane',
            agent_type='control_plane',
            message_type='notification',
            content={
                'event_type': event_type,
                'data': data,
            },
            priority=3,  # High priority for control plane messages
        )
        self.receive_message(message)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a submitted task"""
        return self._pending_tasks.get(task_id)
    
    # ========== Lifecycle (Sync methods) ==========
    
    def start_sync(self):
        """Start the Master Brain"""
        self.state = BrainState.ACTIVE
        # Start background optimization
        self._start_background_optimization()
    
    def pause(self):
        """Pause the Master Brain"""
        self.state = BrainState.PAUSED
    
    def resume(self):
        """Resume the Master Brain"""
        if self.state == BrainState.PAUSED:
            self.state = BrainState.ACTIVE
    
    def shutdown(self):
        """Shutdown the Master Brain"""
        self.state = BrainState.SHUTDOWN
        # Clean up resources
        self._message_queue.clear()
    
    def _start_background_optimization(self):
        """Start background optimization thread"""
        def optimization_loop():
            while self.state == BrainState.ACTIVE:
                try:
                    self.run_optimization_cycle()
                except Exception as e:
                    self._log_error(f"Optimization cycle failed: {e}")
                
                # Run every 5 minutes
                threading.Event().wait(300)
        
        thread = threading.Thread(target=optimization_loop, daemon=True)
        thread.start()


# Celery tasks for Master Brain
def register_celery_tasks():
    """Register Master Brain Celery tasks"""
    from task_queue.celery_app import celery_app
    
    brain = MasterBrain()
    
    @celery_app.task(name='master_brain.optimize_queue')
    def optimize_queue():
        """Periodic queue optimization"""
        brain.run_optimization_cycle()
        return {'status': 'completed', 'timestamp': datetime.utcnow().isoformat()}
    
    @celery_app.task(name='master_brain.collect_metrics')
    def collect_metrics():
        """Collect system metrics"""
        return brain.get_system_status()
    
    @celery_app.task(name='master_brain.receive_agent_message')
    def receive_agent_message(message_data: Dict):
        """Receive a message from an agent"""
        message = AgentMessage(**message_data)
        brain.receive_message(message)
        return {'status': 'received'}
    
    return brain
