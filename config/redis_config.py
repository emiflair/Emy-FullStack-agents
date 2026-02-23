"""
Redis Configuration
Redis connection and caching settings
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import os


class RedisDatabase(int, Enum):
    """Redis database numbers"""
    CELERY_BROKER = 0
    CELERY_RESULTS = 1
    CACHE = 2
    SESSION = 3
    RATE_LIMIT = 4
    PUBSUB = 5
    TASK_QUEUE = 6
    LOCKS = 7


@dataclass
class RedisConfig:
    """Redis configuration"""
    
    # Connection
    host: str = field(default_factory=lambda: os.getenv('REDIS_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('REDIS_PORT', '6379')))
    password: Optional[str] = field(default_factory=lambda: os.getenv('REDIS_PASSWORD'))
    
    # SSL
    ssl: bool = False
    ssl_ca_certs: Optional[str] = None
    
    # Connection pool
    max_connections: int = 10
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    
    # Retry
    retry_on_timeout: bool = True
    retry_on_error: List[Exception] = field(default_factory=list)
    
    # Health check
    health_check_interval: int = 30
    
    def get_url(self, database: RedisDatabase = RedisDatabase.CACHE) -> str:
        """Build Redis URL for specific database"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{database.value}"
        return f"redis://{self.host}:{self.port}/{database.value}"
    
    @property
    def broker_url(self) -> str:
        """Get Celery broker URL"""
        return self.get_url(RedisDatabase.CELERY_BROKER)
    
    @property
    def result_backend_url(self) -> str:
        """Get Celery result backend URL"""
        return self.get_url(RedisDatabase.CELERY_RESULTS)
    
    @property
    def cache_url(self) -> str:
        """Get cache URL"""
        return self.get_url(RedisDatabase.CACHE)
    
    def get_connection_kwargs(self) -> Dict[str, Any]:
        """Get connection parameters"""
        kwargs = {
            'host': self.host,
            'port': self.port,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'socket_keepalive': self.socket_keepalive,
            'retry_on_timeout': self.retry_on_timeout,
            'health_check_interval': self.health_check_interval,
        }
        
        if self.password:
            kwargs['password'] = self.password
        
        if self.ssl:
            kwargs['ssl'] = True
            if self.ssl_ca_certs:
                kwargs['ssl_ca_certs'] = self.ssl_ca_certs
        
        return kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'host': self.host,
            'port': self.port,
            'ssl': self.ssl,
            'max_connections': self.max_connections,
            'socket_timeout': self.socket_timeout,
        }


# Cache settings
CACHE_CONFIG = {
    'default': {
        'ttl': 300,  # 5 minutes
        'prefix': 'emy:cache:',
    },
    'session': {
        'ttl': 86400,  # 24 hours
        'prefix': 'emy:session:',
    },
    'rate_limit': {
        'ttl': 60,  # 1 minute
        'prefix': 'emy:ratelimit:',
    },
    'task': {
        'ttl': 3600,  # 1 hour
        'prefix': 'emy:task:',
    },
    'agent': {
        'ttl': 600,  # 10 minutes
        'prefix': 'emy:agent:',
    },
}


# PubSub channels
PUBSUB_CHANNELS = {
    'agent_events': 'emy:pubsub:agent_events',
    'task_updates': 'emy:pubsub:task_updates',
    'system_events': 'emy:pubsub:system_events',
    'optimization': 'emy:pubsub:optimization',
    'notifications': 'emy:pubsub:notifications',
}


# Lock settings
LOCK_CONFIG = {
    'default_timeout': 30,  # seconds
    'blocking_timeout': 10,  # seconds
    'prefix': 'emy:lock:',
}


def get_redis_config() -> RedisConfig:
    """Get Redis configuration from environment"""
    return RedisConfig()
