"""
Task Router
Routes tasks to appropriate agents based on task type and configuration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Pattern
from enum import Enum
import re
import json


class RouteStrategy(Enum):
    """Routing strategies for task distribution"""
    DIRECT = "direct"           # Route to specific agent
    ROUND_ROBIN = "round_robin" # Distribute evenly across agents
    LEAST_LOADED = "least_loaded"  # Route to agent with least pending tasks
    PRIORITY_BASED = "priority_based"  # Route based on task priority
    CONTENT_BASED = "content_based"    # Route based on task content


@dataclass
class TaskRoute:
    """Definition of a task route"""
    pattern: str                         # Regex pattern to match task names
    target_queue: str                    # Target queue/agent
    strategy: RouteStrategy = RouteStrategy.DIRECT
    priority_override: Optional[int] = None
    transform: Optional[Callable] = None  # Optional payload transformer
    conditions: Optional[Dict[str, Any]] = None  # Additional routing conditions
    fallback_queue: Optional[str] = None
    
    def __post_init__(self):
        self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
    
    def matches(self, task_name: str, payload: Optional[Dict] = None) -> bool:
        """Check if this route matches the task"""
        if not self._compiled_pattern.search(task_name):
            return False
        
        if self.conditions and payload:
            for key, expected in self.conditions.items():
                if key not in payload or payload[key] != expected:
                    return False
        
        return True


class TaskRouter:
    """
    Routes tasks to appropriate queues/agents
    Supports multiple routing strategies and dynamic configuration
    """
    
    # Default routes for agent tasks
    DEFAULT_ROUTES = [
        # Frontend tasks
        TaskRoute(
            pattern=r'(flutter|widget|ui_component|screen|layout)',
            target_queue='frontend',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # Backend tasks
        TaskRoute(
            pattern=r'(api|endpoint|crud|authentication|middleware)',
            target_queue='backend',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # Database tasks
        TaskRoute(
            pattern=r'(database|schema|migration|query|sql|redis|cache)',
            target_queue='database',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # DevOps tasks
        TaskRoute(
            pattern=r'(docker|kubernetes|k8s|deploy|ci|cd|pipeline|infrastructure)',
            target_queue='devops',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # QA tasks
        TaskRoute(
            pattern=r'(test|qa|quality|coverage|validation|automation)',
            target_queue='qa',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # UI/UX tasks
        TaskRoute(
            pattern=r'(design|wireframe|mockup|prototype|ux|user_experience)',
            target_queue='uiux',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # Security tasks
        TaskRoute(
            pattern=r'(security|auth|encrypt|vulnerability|compliance|audit)',
            target_queue='security',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # AI/ML tasks
        TaskRoute(
            pattern=r'(ml|ai|model|predict|train|optimize|content_generate)',
            target_queue='aiml',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # Project management tasks
        TaskRoute(
            pattern=r'(project|task_assign|milestone|sprint|workflow|coordinate)',
            target_queue='project_manager',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # Master Brain tasks
        TaskRoute(
            pattern=r'(master_brain|orchestrate|global_optimize|system_monitor)',
            target_queue='master_brain',
            strategy=RouteStrategy.DIRECT,
        ),
        
        # OpenClaw tasks
        TaskRoute(
            pattern=r'(openclaw|scrape|post|external_api|automation)',
            target_queue='openclaw',
            strategy=RouteStrategy.DIRECT,
        ),
    ]
    
    def __init__(self):
        self.routes: List[TaskRoute] = list(self.DEFAULT_ROUTES)
        self._queue_loads: Dict[str, int] = {}
        self._round_robin_index: Dict[str, int] = {}
        self._custom_routers: Dict[str, Callable] = {}
    
    def add_route(self, route: TaskRoute, priority: int = -1):
        """Add a custom route (higher priority routes checked first)"""
        if priority < 0:
            self.routes.append(route)
        else:
            self.routes.insert(priority, route)
    
    def remove_route(self, pattern: str) -> bool:
        """Remove a route by pattern"""
        for i, route in enumerate(self.routes):
            if route.pattern == pattern:
                self.routes.pop(i)
                return True
        return False
    
    def route(
        self,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Route a task to the appropriate queue
        Returns routing decision with queue name and any transformations
        """
        for route in self.routes:
            if route.matches(task_name, payload):
                target_queue = self._resolve_target(route, task_name, payload)
                
                result = {
                    'queue': target_queue,
                    'strategy': route.strategy.value,
                    'priority': route.priority_override or priority,
                    'payload': payload,
                }
                
                # Apply payload transformation if defined
                if route.transform and payload:
                    result['payload'] = route.transform(payload)
                
                return result
        
        # Default routing
        return {
            'queue': 'medium',  # Default priority queue
            'strategy': RouteStrategy.DIRECT.value,
            'priority': priority,
            'payload': payload,
        }
    
    def _resolve_target(
        self,
        route: TaskRoute,
        task_name: str,
        payload: Optional[Dict],
    ) -> str:
        """Resolve the target queue based on routing strategy"""
        if route.strategy == RouteStrategy.DIRECT:
            return route.target_queue
        
        elif route.strategy == RouteStrategy.ROUND_ROBIN:
            return self._round_robin_select(route.target_queue)
        
        elif route.strategy == RouteStrategy.LEAST_LOADED:
            return self._least_loaded_select(route.target_queue)
        
        elif route.strategy == RouteStrategy.CONTENT_BASED:
            return self._content_based_select(route, payload)
        
        return route.target_queue
    
    def _round_robin_select(self, base_queue: str) -> str:
        """Select queue using round-robin strategy"""
        # For simplicity, return base queue
        # In production, would cycle through multiple workers
        return base_queue
    
    def _least_loaded_select(self, base_queue: str) -> str:
        """Select the least loaded queue"""
        # Would query actual queue loads in production
        return base_queue
    
    def _content_based_select(
        self,
        route: TaskRoute,
        payload: Optional[Dict],
    ) -> str:
        """Select queue based on payload content"""
        if not payload:
            return route.target_queue
        
        # Check for specific content indicators
        if 'urgent' in str(payload).lower():
            return 'critical'
        
        return route.target_queue
    
    def update_queue_load(self, queue: str, load: int):
        """Update the load metric for a queue"""
        self._queue_loads[queue] = load
    
    def register_custom_router(
        self,
        name: str,
        router_func: Callable[[str, Dict], str],
    ):
        """Register a custom routing function"""
        self._custom_routers[name] = router_func
    
    def get_routing_table(self) -> List[Dict[str, Any]]:
        """Get the current routing configuration"""
        return [
            {
                'pattern': route.pattern,
                'target_queue': route.target_queue,
                'strategy': route.strategy.value,
                'priority_override': route.priority_override,
                'fallback_queue': route.fallback_queue,
            }
            for route in self.routes
        ]
    
    def batch_route(
        self,
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Route multiple tasks and group by target queue"""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        
        for task in tasks:
            routing = self.route(
                task_name=task.get('name', ''),
                payload=task.get('payload'),
                priority=task.get('priority'),
            )
            
            queue = routing['queue']
            if queue not in grouped:
                grouped[queue] = []
            
            grouped[queue].append({
                **task,
                'routing': routing,
            })
        
        return grouped


class DynamicRouter:
    """
    Dynamic router that adjusts routing based on system state
    """
    
    def __init__(self, base_router: TaskRouter):
        self.base_router = base_router
        self._overrides: Dict[str, str] = {}
        self._disabled_queues: set = set()
        self._queue_capacities: Dict[str, int] = {}
    
    def set_override(self, pattern: str, target_queue: str):
        """Set a temporary routing override"""
        self._overrides[pattern] = target_queue
    
    def clear_override(self, pattern: str):
        """Clear a routing override"""
        if pattern in self._overrides:
            del self._overrides[pattern]
    
    def disable_queue(self, queue: str):
        """Temporarily disable routing to a queue"""
        self._disabled_queues.add(queue)
    
    def enable_queue(self, queue: str):
        """Re-enable routing to a queue"""
        self._disabled_queues.discard(queue)
    
    def set_queue_capacity(self, queue: str, capacity: int):
        """Set maximum capacity for a queue"""
        self._queue_capacities[queue] = capacity
    
    def route(
        self,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Route with dynamic adjustments"""
        # Check for overrides
        for pattern, target in self._overrides.items():
            if re.search(pattern, task_name, re.IGNORECASE):
                return {
                    'queue': target,
                    'strategy': 'override',
                    'priority': priority,
                    'payload': payload,
                }
        
        # Base routing
        result = self.base_router.route(task_name, payload, priority)
        
        # Check if target queue is disabled
        if result['queue'] in self._disabled_queues:
            # Find fallback
            for route in self.base_router.routes:
                if route.matches(task_name, payload) and route.fallback_queue:
                    result['queue'] = route.fallback_queue
                    result['fallback_used'] = True
                    break
            else:
                result['queue'] = 'medium'  # Default fallback
                result['fallback_used'] = True
        
        return result
