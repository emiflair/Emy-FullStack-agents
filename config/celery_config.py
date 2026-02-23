"""
Celery Configuration
Task queue and worker settings
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import timedelta
import os


@dataclass
class CelerySettings:
    """Celery configuration settings"""
    
    # Broker settings
    broker_url: str = field(
        default_factory=lambda: os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    result_backend: str = field(
        default_factory=lambda: os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    )
    
    # Task settings
    task_serializer: str = 'json'
    result_serializer: str = 'json'
    accept_content: List[str] = field(default_factory=lambda: ['json'])
    timezone: str = 'UTC'
    enable_utc: bool = True
    
    # Task execution
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    task_time_limit: int = 3600  # 1 hour
    task_soft_time_limit: int = 3300  # 55 minutes
    task_default_retry_delay: int = 60
    task_max_retries: int = 3
    
    # Result settings
    result_expires: int = 86400  # 24 hours
    result_extended: bool = True
    
    # Worker settings
    worker_prefetch_multiplier: int = 4
    worker_max_tasks_per_child: int = 1000
    worker_disable_rate_limits: bool = False
    worker_concurrency: int = field(
        default_factory=lambda: int(os.getenv('CELERY_CONCURRENCY', '4'))
    )
    
    # Monitoring
    worker_send_task_events: bool = True
    task_send_sent_event: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Celery config dict"""
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
            'task_default_retry_delay': self.task_default_retry_delay,
            'result_expires': self.result_expires,
            'result_extended': self.result_extended,
            'worker_prefetch_multiplier': self.worker_prefetch_multiplier,
            'worker_max_tasks_per_child': self.worker_max_tasks_per_child,
            'worker_concurrency': self.worker_concurrency,
            'worker_send_task_events': self.worker_send_task_events,
            'task_send_sent_event': self.task_send_sent_event,
        }


# Task routing configuration
TASK_ROUTES = {
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
    
    # High priority tasks
    'tasks.critical.*': {'queue': 'critical'},
    
    # Default queue
    '*': {'queue': 'default'},
}


# Queue configurations
QUEUE_CONFIG = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
        'priority': 5,
    },
    'critical': {
        'exchange': 'critical',
        'routing_key': 'critical',
        'priority': 10,
    },
    'frontend': {
        'exchange': 'agents',
        'routing_key': 'agents.frontend',
        'priority': 7,
    },
    'backend': {
        'exchange': 'agents',
        'routing_key': 'agents.backend',
        'priority': 7,
    },
    'database': {
        'exchange': 'agents',
        'routing_key': 'agents.database',
        'priority': 8,
    },
    'devops': {
        'exchange': 'agents',
        'routing_key': 'agents.devops',
        'priority': 6,
    },
    'qa': {
        'exchange': 'agents',
        'routing_key': 'agents.qa',
        'priority': 5,
    },
    'uiux': {
        'exchange': 'agents',
        'routing_key': 'agents.uiux',
        'priority': 5,
    },
    'security': {
        'exchange': 'agents',
        'routing_key': 'agents.security',
        'priority': 9,
    },
    'aiml': {
        'exchange': 'agents',
        'routing_key': 'agents.aiml',
        'priority': 7,
    },
    'project_manager': {
        'exchange': 'agents',
        'routing_key': 'agents.project_manager',
        'priority': 8,
    },
    'master_brain': {
        'exchange': 'master',
        'routing_key': 'master.brain',
        'priority': 9,
    },
}


# Beat schedule for periodic tasks
BEAT_SCHEDULE = {
    'health-check': {
        'task': 'master_brain.health_check',
        'schedule': timedelta(minutes=1),
        'options': {'queue': 'master_brain'},
    },
    'optimization-cycle': {
        'task': 'master_brain.run_optimization',
        'schedule': timedelta(minutes=5),
        'options': {'queue': 'master_brain'},
    },
    'feedback-collection': {
        'task': 'master_brain.collect_feedback',
        'schedule': timedelta(minutes=2),
        'options': {'queue': 'master_brain'},
    },
    'task-cleanup': {
        'task': 'tasks.cleanup_old_tasks',
        'schedule': timedelta(hours=1),
        'options': {'queue': 'default'},
    },
    'metrics-aggregation': {
        'task': 'monitoring.aggregate_metrics',
        'schedule': timedelta(minutes=5),
        'options': {'queue': 'default'},
    },
    'scheduled-posts': {
        'task': 'integrations.process_scheduled_posts',
        'schedule': timedelta(minutes=1),
        'options': {'queue': 'default'},
    },
}


def get_celery_settings() -> CelerySettings:
    """Get Celery configuration from environment"""
    return CelerySettings()
