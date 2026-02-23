"""
Automation Engine
Workflow automation for OpenClaw integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import uuid
import re


class TriggerType(Enum):
    """Types of automation triggers"""
    SCHEDULE = "schedule"         # Time-based
    WEBHOOK = "webhook"           # External webhook
    EVENT = "event"               # Internal event
    CONDITION = "condition"       # Condition-based
    MANUAL = "manual"             # Manual trigger


class ActionType(Enum):
    """Types of automation actions"""
    SCRAPE = "scrape"
    POST = "post"
    API_CALL = "api_call"
    TRANSFORM = "transform"
    FILTER = "filter"
    DELAY = "delay"
    BRANCH = "branch"
    LOOP = "loop"
    NOTIFY = "notify"
    CUSTOM = "custom"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Trigger:
    """Workflow trigger configuration"""
    trigger_type: TriggerType
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.trigger_type.value,
            'config': self.config,
            'enabled': self.enabled,
        }


@dataclass
class Action:
    """Workflow action configuration"""
    action_id: str
    action_type: ActionType
    config: Dict[str, Any] = field(default_factory=dict)
    on_success: Optional[str] = None  # Next action ID
    on_failure: Optional[str] = None  # Action ID on failure
    retry_count: int = 0
    timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'type': self.action_type.value,
            'config': self.config,
            'on_success': self.on_success,
            'on_failure': self.on_failure,
            'retry_count': self.retry_count,
            'timeout': self.timeout,
        }


@dataclass
class AutomationTask:
    """A single automation task"""
    task_id: str
    workflow_id: str
    action: Action
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_attempt: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'workflow_id': self.workflow_id,
            'action': self.action.to_dict(),
            'status': self.status.value,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_attempt': self.retry_attempt,
        }


@dataclass
class AutomationWorkflow:
    """Automation workflow definition"""
    workflow_id: str
    name: str
    description: str = ""
    triggers: List[Trigger] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    start_action: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'triggers': [t.to_dict() for t in self.triggers],
            'actions': [a.to_dict() for a in self.actions],
            'start_action': self.start_action,
            'variables': self.variables,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Get action by ID"""
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None


@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_action: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    tasks: List[AutomationTask] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'workflow_id': self.workflow_id,
            'status': self.status.value,
            'current_action': self.current_action,
            'tasks': [t.to_dict() for t in self.tasks],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }


class AutomationEngine:
    """
    Workflow automation engine
    Executes workflows with various triggers and actions
    """
    
    def __init__(self):
        self._workflows: Dict[str, AutomationWorkflow] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._action_handlers: Dict[ActionType, Callable] = {}
        self._trigger_handlers: Dict[TriggerType, Callable] = {}
        self._scheduled_triggers: Dict[str, Dict[str, Any]] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default action handlers"""
        self._action_handlers = {
            ActionType.SCRAPE: self._handle_scrape,
            ActionType.POST: self._handle_post,
            ActionType.API_CALL: self._handle_api_call,
            ActionType.TRANSFORM: self._handle_transform,
            ActionType.FILTER: self._handle_filter,
            ActionType.DELAY: self._handle_delay,
            ActionType.BRANCH: self._handle_branch,
            ActionType.LOOP: self._handle_loop,
            ActionType.NOTIFY: self._handle_notify,
            ActionType.CUSTOM: self._handle_custom,
        }
    
    def register_action_handler(self, action_type: ActionType, handler: Callable):
        """Register a custom action handler"""
        self._action_handlers[action_type] = handler
    
    def create_workflow(
        self,
        name: str,
        description: str = "",
        triggers: Optional[List[Trigger]] = None,
        actions: Optional[List[Action]] = None,
        start_action: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> AutomationWorkflow:
        """Create a new workflow"""
        workflow = AutomationWorkflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            triggers=triggers or [],
            actions=actions or [],
            start_action=start_action,
            variables=variables or {},
        )
        
        # Set start action if not specified
        if not workflow.start_action and workflow.actions:
            workflow.start_action = workflow.actions[0].action_id
        
        self._workflows[workflow.workflow_id] = workflow
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[AutomationWorkflow]:
        """Get a workflow by ID"""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self, enabled_only: bool = False) -> List[AutomationWorkflow]:
        """List all workflows"""
        workflows = list(self._workflows.values())
        if enabled_only:
            workflows = [w for w in workflows if w.enabled]
        return workflows
    
    def update_workflow(
        self,
        workflow_id: str,
        **updates,
    ) -> Optional[AutomationWorkflow]:
        """Update a workflow"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.utcnow()
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        run_async: bool = False,
    ) -> WorkflowExecution:
        """Execute a workflow"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if not workflow.enabled:
            raise ValueError(f"Workflow {workflow_id} is disabled")
        
        # Create execution instance
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            context={
                **workflow.variables,
                'input': input_data or {},
            },
        )
        
        self._executions[execution.execution_id] = execution
        
        if run_async:
            asyncio.create_task(self._run_workflow(workflow, execution))
        else:
            await self._run_workflow(workflow, execution)
        
        return execution
    
    async def _run_workflow(
        self,
        workflow: AutomationWorkflow,
        execution: WorkflowExecution,
    ):
        """Run a workflow execution"""
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.utcnow()
        
        try:
            current_action_id = workflow.start_action
            
            while current_action_id:
                action = workflow.get_action(current_action_id)
                if not action:
                    break
                
                execution.current_action = current_action_id
                
                # Execute action
                task = await self._execute_action(execution, action)
                execution.tasks.append(task)
                
                if task.status == WorkflowStatus.FAILED:
                    if action.on_failure:
                        current_action_id = action.on_failure
                    else:
                        execution.status = WorkflowStatus.FAILED
                        execution.error = task.error
                        break
                else:
                    # Update context with output
                    execution.context[action.action_id] = task.output_data
                    current_action_id = action.on_success
            
            if execution.status != WorkflowStatus.FAILED:
                execution.status = WorkflowStatus.COMPLETED
                
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
        
        finally:
            execution.completed_at = datetime.utcnow()
    
    async def _execute_action(
        self,
        execution: WorkflowExecution,
        action: Action,
    ) -> AutomationTask:
        """Execute a single action"""
        task = AutomationTask(
            task_id=str(uuid.uuid4()),
            workflow_id=execution.workflow_id,
            action=action,
            input_data=dict(execution.context),
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        
        handler = self._action_handlers.get(action.action_type)
        if not handler:
            task.status = WorkflowStatus.FAILED
            task.error = f"No handler for action type: {action.action_type.value}"
            task.completed_at = datetime.utcnow()
            return task
        
        # Retry loop
        for attempt in range(action.retry_count + 1):
            task.retry_attempt = attempt
            
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(action.config, execution.context),
                    timeout=action.timeout,
                )
                
                task.output_data = result or {}
                task.status = WorkflowStatus.COMPLETED
                break
                
            except asyncio.TimeoutError:
                task.error = 'Action timeout'
                task.status = WorkflowStatus.FAILED
            except Exception as e:
                task.error = str(e)
                task.status = WorkflowStatus.FAILED
            
            if attempt < action.retry_count:
                await asyncio.sleep(1 * (attempt + 1))
        
        task.completed_at = datetime.utcnow()
        return task
    
    # ========== Action Handlers ==========
    
    async def _handle_scrape(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle scrape action"""
        from .scraper import WebScraper, Selector, ScrapingMethod, ContentType
        
        scraper = WebScraper()
        
        url = self._resolve_template(config.get('url', ''), context)
        selectors = []
        
        for sel_config in config.get('selectors', []):
            selectors.append(Selector(
                name=sel_config['name'],
                selector=sel_config['selector'],
                method=ScrapingMethod(sel_config.get('method', 'css')),
                content_type=ContentType(sel_config.get('content_type', 'text')),
                multiple=sel_config.get('multiple', False),
            ))
        
        result = await scraper.scrape(url, selectors)
        await scraper.close()
        
        if not result.success:
            raise Exception(result.error)
        
        return result.data
    
    async def _handle_post(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle post action"""
        from .poster import ContentPoster, PostContent, Platform
        
        poster = ContentPoster()
        
        platform = Platform(config.get('platform', 'twitter'))
        content = PostContent(
            text=self._resolve_template(config.get('text', ''), context),
            hashtags=config.get('hashtags', []),
            link=config.get('link'),
        )
        
        result = await poster.post(platform, content)
        
        return result.to_dict()
    
    async def _handle_api_call(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle API call action"""
        import aiohttp
        
        method = config.get('method', 'GET').upper()
        url = self._resolve_template(config.get('url', ''), context)
        headers = config.get('headers', {})
        body = config.get('body')
        
        if body:
            body = json.loads(self._resolve_template(json.dumps(body), context))
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if method in ['POST', 'PUT', 'PATCH'] else None,
                params=body if method == 'GET' else None,
            ) as response:
                data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                return {
                    'status_code': response.status,
                    'data': data,
                    'headers': dict(response.headers),
                }
    
    async def _handle_transform(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle data transformation action"""
        input_path = config.get('input_path', 'input')
        output_key = config.get('output_key', 'result')
        transformations = config.get('transformations', [])
        
        # Get input data
        data = self._get_nested_value(context, input_path)
        
        # Apply transformations
        for transform in transformations:
            transform_type = transform.get('type')
            
            if transform_type == 'map':
                mapping = transform.get('mapping', {})
                if isinstance(data, list):
                    data = [
                        {mapping.get(k, k): v for k, v in item.items()}
                        if isinstance(item, dict) else item
                        for item in data
                    ]
            
            elif transform_type == 'filter':
                condition = transform.get('condition')
                if isinstance(data, list) and condition:
                    data = [
                        item for item in data
                        if self._evaluate_condition(item, condition)
                    ]
            
            elif transform_type == 'extract':
                key = transform.get('key')
                if key and isinstance(data, dict):
                    data = data.get(key)
            
            elif transform_type == 'template':
                template = transform.get('template', '')
                data = self._resolve_template(template, {'data': data, **context})
        
        return {output_key: data}
    
    async def _handle_filter(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle filter action"""
        condition = config.get('condition', {})
        passes = self._evaluate_condition(context, condition)
        
        return {'passes': passes, 'data': context if passes else None}
    
    async def _handle_delay(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle delay action"""
        seconds = config.get('seconds', 1)
        await asyncio.sleep(seconds)
        return {'delayed': seconds}
    
    async def _handle_branch(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle branching action"""
        condition = config.get('condition', {})
        true_action = config.get('true_action')
        false_action = config.get('false_action')
        
        result = self._evaluate_condition(context, condition)
        
        return {
            'branch_taken': 'true' if result else 'false',
            'next_action': true_action if result else false_action,
        }
    
    async def _handle_loop(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle loop action"""
        items_path = config.get('items_path', 'items')
        items = self._get_nested_value(context, items_path)
        
        if not isinstance(items, list):
            items = [items]
        
        results = []
        for i, item in enumerate(items):
            results.append({
                'index': i,
                'item': item,
            })
        
        return {'iterations': results, 'count': len(results)}
    
    async def _handle_notify(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle notification action"""
        # This would integrate with notification services
        message = self._resolve_template(config.get('message', ''), context)
        channel = config.get('channel', 'default')
        
        return {
            'notified': True,
            'channel': channel,
            'message': message,
        }
    
    async def _handle_custom(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle custom action"""
        handler_name = config.get('handler')
        
        if handler_name and hasattr(self, f'_custom_{handler_name}'):
            handler = getattr(self, f'_custom_{handler_name}')
            return await handler(config, context)
        
        return {'custom': True, 'config': config}
    
    # ========== Utilities ==========
    
    def _resolve_template(self, template: str, context: Dict[str, Any]) -> str:
        """Resolve template variables"""
        def replace(match):
            path = match.group(1)
            value = self._get_nested_value(context, path)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(r'\{\{([^}]+)\}\}', replace, template)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dict using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)] if int(key) < len(value) else None
            else:
                return None
        
        return value
    
    def _evaluate_condition(self, data: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition against data"""
        operator = condition.get('operator', 'eq')
        field = condition.get('field')
        value = condition.get('value')
        
        # Get field value
        if field and isinstance(data, dict):
            actual = self._get_nested_value(data, field)
        else:
            actual = data
        
        # Compare
        if operator == 'eq':
            return actual == value
        elif operator == 'ne':
            return actual != value
        elif operator == 'gt':
            return actual > value
        elif operator == 'gte':
            return actual >= value
        elif operator == 'lt':
            return actual < value
        elif operator == 'lte':
            return actual <= value
        elif operator == 'contains':
            return value in str(actual)
        elif operator == 'not_contains':
            return value not in str(actual)
        elif operator == 'exists':
            return actual is not None
        elif operator == 'not_exists':
            return actual is None
        elif operator == 'in':
            return actual in value
        elif operator == 'not_in':
            return actual not in value
        elif operator == 'and':
            conditions = condition.get('conditions', [])
            return all(self._evaluate_condition(data, c) for c in conditions)
        elif operator == 'or':
            conditions = condition.get('conditions', [])
            return any(self._evaluate_condition(data, c) for c in conditions)
        
        return False
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self._executions.get(execution_id)
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
    ) -> List[WorkflowExecution]:
        """List executions"""
        executions = list(self._executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        return sorted(
            executions,
            key=lambda e: e.started_at or datetime.min,
            reverse=True,
        )[:limit]
