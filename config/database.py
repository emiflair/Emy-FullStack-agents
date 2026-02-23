"""
Database Configuration
PostgreSQL and SQLAlchemy settings
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import os


class DatabaseDriver(str, Enum):
    """Database drivers"""
    POSTGRESQL = "postgresql"
    POSTGRESQL_ASYNCPG = "postgresql+asyncpg"
    MYSQL = "mysql"
    SQLITE = "sqlite"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    
    # Connection
    driver: DatabaseDriver = DatabaseDriver.POSTGRESQL
    host: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '5432')))
    database: str = field(default_factory=lambda: os.getenv('DB_NAME', 'emydb'))
    username: str = field(default_factory=lambda: os.getenv('DB_USER', 'user'))
    password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', 'password'))
    
    # Pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    
    # Query settings
    echo: bool = False
    echo_pool: bool = False
    
    # SSL
    ssl_mode: Optional[str] = None
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    
    @property
    def url(self) -> str:
        """Build database URL"""
        return f"{self.driver.value}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """Build async database URL"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_engine_args(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine arguments"""
        args = {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'echo': self.echo,
            'echo_pool': self.echo_pool,
        }
        
        if self.ssl_mode:
            args['connect_args'] = {
                'sslmode': self.ssl_mode,
            }
            if self.ssl_ca:
                args['connect_args']['sslrootcert'] = self.ssl_ca
        
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'driver': self.driver.value,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'ssl_mode': self.ssl_mode,
        }


# Database table configurations
DATABASE_TABLES = {
    'users': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['email', 'created_at'],
    },
    'sellers': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['user_id', 'platform', 'created_at'],
    },
    'campaigns': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['seller_id', 'status', 'start_date'],
    },
    'content_logs': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['campaign_id', 'content_type', 'created_at'],
    },
    'tasks': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['status', 'priority', 'assigned_agent', 'created_at'],
    },
    'agent_logs': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['agent_id', 'log_level', 'timestamp'],
    },
    'workflows': {
        'schema': 'public',
        'primary_key': 'id',
        'indexes': ['status', 'created_at'],
    },
}


# Migration settings
MIGRATION_CONFIG = {
    'script_location': 'migrations',
    'version_table': 'alembic_version',
    'truncate_slug_length': 40,
    'revision_environment': True,
}


def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment"""
    return DatabaseConfig()
