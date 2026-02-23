"""
Task Registry
Central registry for all tasks in the Emy-FullStack system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Type
from datetime import datetime, timedelta
from enum import Enum
import threading
import json
import functools


class TaskState(Enum):
    """Task execution states"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


@dataclass
class RegisteredTask:
    """Information about a registered task"""
    name: str
    func: Callable
    queue: str
    description: str = ""
    rate_limit: Optional[str] = None
    time_limit: Optional[int] = None
    max_retries: int = 3
    retry_backoff: bool = True
    priority: int = 5
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'queue': self.queue,
            'description': self.description,
            'rate_limit': self.rate_limit,
            'time_limit': self.time_limit,
            'max_retries': self.max_retries,
            'retry_backoff': self.retry_backoff,
            'priority': self.priority,
            'tags': self.tags,
        }


@dataclass
class TaskExecution:
    """Record of a task execution"""
    task_id: str
    task_name: str
    state: TaskState
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    worker_id: Optional[str] = None
    queue: Optional[str] = None
    args: Optional[List] = None
    kwargs: Optional[Dict] = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'state': self.state.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_seconds': self.duration.total_seconds() if self.duration else None,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'retry_count': self.retry_count,
            'worker_id': self.worker_id,
            'queue': self.queue,
        }


class TaskRegistry:
    """
    Central registry for managing task definitions and executions
    """
    
    _tasks: Dict[str, RegisteredTask] = {}
    _executions: Dict[str, TaskExecution] = {}
    _lock = threading.Lock()
    _metrics: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(
        cls,
        name: str,
        queue: str = 'medium',
        description: str = "",
        rate_limit: Optional[str] = None,
        time_limit: Optional[int] = None,
        max_retries: int = 3,
        retry_backoff: bool = True,
        priority: int = 5,
        tags: Optional[List[str]] = None,
    ) -> Callable:
        """Decorator to register a task"""
        def decorator(func: Callable) -> Callable:
            task = RegisteredTask(
                name=name,
                func=func,
                queue=queue,
                description=description or func.__doc__ or "",
                rate_limit=rate_limit,
                time_limit=time_limit,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                priority=priority,
                tags=tags or [],
            )
            
            with cls._lock:
                cls._tasks[name] = task
                
                # Initialize metrics
                cls._metrics[name] = {
                    'total_runs': 0,
                    'successes': 0,
                    'failures': 0,
                    'retries': 0,
                    'total_duration': 0.0,
                    'last_run': None,
                }
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            wrapper._task_name = name
            wrapper._registered_task = task
            return wrapper
        
        return decorator
    
    @classmethod
    def get_task(cls, name: str) -> Optional[RegisteredTask]:
        """Get a registered task by name"""
        return cls._tasks.get(name)
    
    @classmethod
    def list_tasks(
        cls,
        queue: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[RegisteredTask]:
        """List registered tasks with optional filtering"""
        tasks = list(cls._tasks.values())
        
        if queue:
            tasks = [t for t in tasks if t.queue == queue]
        
        if tag:
            tasks = [t for t in tasks if tag in t.tags]
        
        return tasks
    
    @classmethod
    def record_start(
        cls,
        task_id: str,
        task_name: str,
        worker_id: Optional[str] = None,
        queue: Optional[str] = None,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
    ):
        """Record task start"""
        execution = TaskExecution(
            task_id=task_id,
            task_name=task_name,
            state=TaskState.STARTED,
            started_at=datetime.utcnow(),
            worker_id=worker_id,
            queue=queue,
            args=args,
            kwargs=kwargs,
        )
        
        with cls._lock:
            cls._executions[task_id] = execution
    
    @classmethod
    def record_success(cls, task_id: str, task_name: str, result: Any = None):
        """Record successful task completion"""
        with cls._lock:
            if task_id in cls._executions:
                execution = cls._executions[task_id]
                execution.state = TaskState.SUCCESS
                execution.finished_at = datetime.utcnow()
                execution.result = result
                
                # Update metrics
                if task_name in cls._metrics:
                    metrics = cls._metrics[task_name]
                    metrics['total_runs'] += 1
                    metrics['successes'] += 1
                    metrics['last_run'] = datetime.utcnow().isoformat()
                    
                    if execution.duration:
                        metrics['total_duration'] += execution.duration.total_seconds()
    
    @classmethod
    def record_failure(cls, task_id: str, task_name: str, error: str):
        """Record task failure"""
        with cls._lock:
            if task_id in cls._executions:
                execution = cls._executions[task_id]
                execution.state = TaskState.FAILURE
                execution.finished_at = datetime.utcnow()
                execution.error = error
                
                # Update metrics
                if task_name in cls._metrics:
                    metrics = cls._metrics[task_name]
                    metrics['total_runs'] += 1
                    metrics['failures'] += 1
                    metrics['last_run'] = datetime.utcnow().isoformat()
    
    @classmethod
    def record_retry(cls, task_id: str, task_name: str, error: str):
        """Record task retry"""
        with cls._lock:
            if task_id in cls._executions:
                execution = cls._executions[task_id]
                execution.state = TaskState.RETRY
                execution.retry_count += 1
                execution.error = error
                
                # Update metrics
                if task_name in cls._metrics:
                    cls._metrics[task_name]['retries'] += 1
    
    @classmethod
    def get_execution(cls, task_id: str) -> Optional[TaskExecution]:
        """Get execution record by task ID"""
        return cls._executions.get(task_id)
    
    @classmethod
    def get_executions(
        cls,
        task_name: Optional[str] = None,
        state: Optional[TaskState] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TaskExecution]:
        """Get execution records with filtering"""
        executions = list(cls._executions.values())
        
        if task_name:
            executions = [e for e in executions if e.task_name == task_name]
        
        if state:
            executions = [e for e in executions if e.state == state]
        
        if since:
            executions = [e for e in executions 
                         if e.started_at and e.started_at >= since]
        
        # Sort by start time, newest first
        executions.sort(key=lambda e: e.started_at or datetime.min, reverse=True)
        
        return executions[:limit]
    
    @classmethod
    def get_metrics(cls, task_name: Optional[str] = None) -> Dict[str, Any]:
        """Get task metrics"""
        if task_name:
            metrics = cls._metrics.get(task_name, {})
            if metrics and metrics['total_runs'] > 0:
                metrics['avg_duration'] = metrics['total_duration'] / metrics['total_runs']
                metrics['success_rate'] = metrics['successes'] / metrics['total_runs']
            return {task_name: metrics}
        
        result = {}
        for name, metrics in cls._metrics.items():
            m = dict(metrics)
            if m['total_runs'] > 0:
                m['avg_duration'] = m['total_duration'] / m['total_runs']
                m['success_rate'] = m['successes'] / m['total_runs']
            result[name] = m
        
        return result
    
    @classmethod
    def cleanup_old_executions(cls, older_than: timedelta = timedelta(hours=24)):
        """Remove old execution records"""
        cutoff = datetime.utcnow() - older_than
        
        with cls._lock:
            to_remove = [
                task_id for task_id, execution in cls._executions.items()
                if execution.finished_at and execution.finished_at < cutoff
            ]
            
            for task_id in to_remove:
                del cls._executions[task_id]
        
        return len(to_remove)
    
    @classmethod
    def reset_metrics(cls, task_name: Optional[str] = None):
        """Reset task metrics"""
        with cls._lock:
            if task_name:
                if task_name in cls._metrics:
                    cls._metrics[task_name] = {
                        'total_runs': 0,
                        'successes': 0,
                        'failures': 0,
                        'retries': 0,
                        'total_duration': 0.0,
                        'last_run': None,
                    }
            else:
                for name in cls._metrics:
                    cls._metrics[name] = {
                        'total_runs': 0,
                        'successes': 0,
                        'failures': 0,
                        'retries': 0,
                        'total_duration': 0.0,
                        'last_run': None,
                    }


# Predefined task decorators for common patterns
def frontend_task(name: str, **kwargs):
    """Register a frontend task"""
    return TaskRegistry.register(name=name, queue='frontend', tags=['frontend'], **kwargs)


def backend_task(name: str, **kwargs):
    """Register a backend task"""
    return TaskRegistry.register(name=name, queue='backend', tags=['backend'], **kwargs)


def database_task(name: str, **kwargs):
    """Register a database task"""
    return TaskRegistry.register(name=name, queue='database', tags=['database'], **kwargs)


def devops_task(name: str, **kwargs):
    """Register a DevOps task"""
    return TaskRegistry.register(name=name, queue='devops', tags=['devops'], **kwargs)


def qa_task(name: str, **kwargs):
    """Register a QA task"""
    return TaskRegistry.register(name=name, queue='qa', tags=['qa'], **kwargs)


def security_task(name: str, **kwargs):
    """Register a security task"""
    return TaskRegistry.register(name=name, queue='security', tags=['security'], **kwargs)


def aiml_task(name: str, **kwargs):
    """Register an AI/ML task"""
    return TaskRegistry.register(name=name, queue='aiml', tags=['aiml'], **kwargs)


def project_task(name: str, **kwargs):
    """Register a project management task"""
    return TaskRegistry.register(name=name, queue='project_manager', tags=['project'], **kwargs)


def critical_task(name: str, **kwargs):
    """Register a critical priority task"""
    return TaskRegistry.register(name=name, queue='critical', priority=10, tags=['critical'], **kwargs)
