"""
Celery Application Configuration
Centralized task queue for all Emy-FullStack agents
"""

from celery import Celery
from kombu import Queue, Exchange
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import os


@dataclass
class CeleryConfig:
    """Celery configuration settings"""
    broker_url: str = field(default_factory=lambda: os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
    result_backend: str = field(default_factory=lambda: os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'))
    task_serializer: str = 'json'
    result_serializer: str = 'json'
    accept_content: List[str] = field(default_factory=lambda: ['json'])
    timezone: str = 'UTC'
    enable_utc: bool = True
    
    # Task execution settings
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    task_time_limit: int = 3600  # 1 hour
    task_soft_time_limit: int = 3300  # 55 minutes
    
    # Worker settings
    worker_prefetch_multiplier: int = 4
    worker_concurrency: int = field(default_factory=lambda: os.cpu_count() or 4)
    worker_max_tasks_per_child: int = 1000
    
    # Result settings
    result_expires: int = 86400  # 24 hours
    result_extended: bool = True
    
    # Rate limiting
    task_default_rate_limit: str = '100/m'
    
    # Retry settings
    task_default_retry_delay: int = 60
    task_max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'broker_url': self.broker_url,
            'result_backend': self.result_backend,
            'task_serializer': self.task_serializer,
            'result_serializer': self.result_serializer,
            'accept_content': self.accept_content,
            'timezone': self.timezone,
            'enable_utc': self.enable_utc,
            'task_acks_late': self.task_acks_late,
            'task_reject_on_worker_lost': self.task_reject_on_worker_lost,
            'task_time_limit': self.task_time_limit,
            'task_soft_time_limit': self.task_soft_time_limit,
            'worker_prefetch_multiplier': self.worker_prefetch_multiplier,
            'worker_concurrency': self.worker_concurrency,
            'worker_max_tasks_per_child': self.worker_max_tasks_per_child,
            'result_expires': self.result_expires,
            'result_extended': self.result_extended,
            'task_default_rate_limit': self.task_default_rate_limit,
            'task_default_retry_delay': self.task_default_retry_delay,
            'task_max_retries': self.task_max_retries,
        }


# Define exchanges for different task types
default_exchange = Exchange('default', type='direct')
priority_exchange = Exchange('priority', type='direct')
broadcast_exchange = Exchange('broadcast', type='fanout')

# Define queues for each agent type
AGENT_QUEUES = [
    # Priority queues
    Queue('critical', priority_exchange, routing_key='critical', queue_arguments={'x-max-priority': 10}),
    Queue('high', priority_exchange, routing_key='high', queue_arguments={'x-max-priority': 7}),
    Queue('medium', priority_exchange, routing_key='medium', queue_arguments={'x-max-priority': 5}),
    Queue('low', priority_exchange, routing_key='low', queue_arguments={'x-max-priority': 3}),
    
    # Agent-specific queues
    Queue('frontend', default_exchange, routing_key='frontend'),
    Queue('backend', default_exchange, routing_key='backend'),
    Queue('database', default_exchange, routing_key='database'),
    Queue('devops', default_exchange, routing_key='devops'),
    Queue('qa', default_exchange, routing_key='qa'),
    Queue('uiux', default_exchange, routing_key='uiux'),
    Queue('security', default_exchange, routing_key='security'),
    Queue('aiml', default_exchange, routing_key='aiml'),
    Queue('project_manager', default_exchange, routing_key='project_manager'),
    
    # Special queues
    Queue('master_brain', default_exchange, routing_key='master_brain'),
    Queue('openclaw', default_exchange, routing_key='openclaw'),
    Queue('broadcast', broadcast_exchange),
]

# Initialize Celery app
celery_app = Celery('emy_fullstack')

# Apply configuration
config = CeleryConfig()
celery_app.conf.update(config.to_dict())

# Set up queues
celery_app.conf.task_queues = AGENT_QUEUES
celery_app.conf.task_default_queue = 'medium'
celery_app.conf.task_default_exchange = 'priority'
celery_app.conf.task_default_routing_key = 'medium'

# Task routing configuration
celery_app.conf.task_routes = {
    # Frontend tasks
    'agents.frontend.*': {'queue': 'frontend'},
    'tasks.frontend.*': {'queue': 'frontend'},
    
    # Backend tasks
    'agents.backend.*': {'queue': 'backend'},
    'tasks.backend.*': {'queue': 'backend'},
    
    # Database tasks
    'agents.database.*': {'queue': 'database'},
    'tasks.database.*': {'queue': 'database'},
    
    # DevOps tasks
    'agents.devops.*': {'queue': 'devops'},
    'tasks.devops.*': {'queue': 'devops'},
    
    # QA tasks
    'agents.qa.*': {'queue': 'qa'},
    'tasks.qa.*': {'queue': 'qa'},
    
    # UI/UX tasks
    'agents.uiux.*': {'queue': 'uiux'},
    'tasks.uiux.*': {'queue': 'uiux'},
    
    # Security tasks
    'agents.security.*': {'queue': 'security'},
    'tasks.security.*': {'queue': 'security'},
    
    # AI/ML tasks
    'agents.aiml.*': {'queue': 'aiml'},
    'tasks.aiml.*': {'queue': 'aiml'},
    
    # Project Manager tasks
    'agents.project_manager.*': {'queue': 'project_manager'},
    'tasks.project_manager.*': {'queue': 'project_manager'},
    
    # Master Brain tasks
    'master_brain.*': {'queue': 'master_brain'},
    
    # OpenClaw tasks
    'openclaw.*': {'queue': 'openclaw'},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'health-check-every-minute': {
        'task': 'task_queue.tasks.health_check',
        'schedule': 60.0,
    },
    'cleanup-expired-results-hourly': {
        'task': 'task_queue.tasks.cleanup_expired_results',
        'schedule': 3600.0,
    },
    'optimize-task-queue-every-5-minutes': {
        'task': 'master_brain.optimize_queue',
        'schedule': 300.0,
    },
    'collect-agent-metrics-every-30-seconds': {
        'task': 'master_brain.collect_metrics',
        'schedule': 30.0,
    },
}


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task class with retry and error handling"""
    
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        from task_queue.task_registry import TaskRegistry
        TaskRegistry.record_success(task_id, self.name)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        from task_queue.task_registry import TaskRegistry
        TaskRegistry.record_failure(task_id, self.name, str(exc))
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        from task_queue.task_registry import TaskRegistry
        TaskRegistry.record_retry(task_id, self.name, str(exc))


# Register base task
celery_app.Task = BaseTask


def get_celery_app() -> Celery:
    """Get the configured Celery application"""
    return celery_app


def configure_celery(custom_config: Optional[Dict[str, Any]] = None) -> Celery:
    """Configure Celery with custom settings"""
    if custom_config:
        celery_app.conf.update(custom_config)
    return celery_app
