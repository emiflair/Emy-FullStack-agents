# Task Queue System
# Centralized Celery-based task orchestration for Emy-FullStack agents

from .celery_app import celery_app, CeleryConfig
from .task_router import TaskRouter, TaskRoute
from .priority_queue import PriorityTaskQueue, TaskPriority, QueuedTask
from .worker_manager import WorkerManager, WorkerPool
from .task_registry import TaskRegistry, RegisteredTask

# Aliases for backward compatibility
TaskQueue = PriorityTaskQueue
Task = QueuedTask

__all__ = [
    'celery_app',
    'CeleryConfig',
    'TaskRouter',
    'TaskRoute',
    'PriorityTaskQueue',
    'TaskPriority',
    'QueuedTask',
    'WorkerManager',
    'WorkerPool',
    'TaskRegistry',
    'RegisteredTask',
    # Aliases
    'TaskQueue',
    'Task',
]
