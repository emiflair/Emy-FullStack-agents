"""
Main Settings Configuration
Central configuration using Pydantic Settings
"""

from functools import lru_cache
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings
import os


class Environment(str, Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """
    Main application settings
    Values are loaded from environment variables
    """
    
    # Application
    app_name: str = Field(default="Emy-FullStack-Agents", env="APP_NAME")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    api_docs_enabled: bool = Field(default=True, env="API_DOCS_ENABLED")
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/emydb",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_url: str = Field(default="redis://localhost:6379/1", env="REDIS_CACHE_URL")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_RESULT_BACKEND"
    )
    celery_task_timeout: int = Field(default=3600, env="CELERY_TASK_TIMEOUT")
    
    # Authentication
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # OpenClaw
    openclaw_base_url: str = Field(
        default="https://api.openclaw.io/v1",
        env="OPENCLAW_BASE_URL"
    )
    openclaw_api_key: Optional[str] = Field(default=None, env="OPENCLAW_API_KEY")
    
    # Agent Settings
    agent_concurrency: int = Field(default=4, env="AGENT_CONCURRENCY")
    agent_timeout: int = Field(default=300, env="AGENT_TIMEOUT")
    agent_retry_count: int = Field(default=3, env="AGENT_RETRY_COUNT")
    
    # Master Brain
    optimization_interval: int = Field(default=60, env="OPTIMIZATION_INTERVAL")
    feedback_collection_interval: int = Field(default=30, env="FEEDBACK_INTERVAL")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    jaeger_host: Optional[str] = Field(default=None, env="JAEGER_HOST")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # File Storage
    storage_backend: str = Field(default="local", env="STORAGE_BACKEND")
    storage_path: str = Field(default="./storage", env="STORAGE_PATH")
    aws_s3_bucket: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        return self.environment == Environment.TESTING
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dict"""
        return {
            'url': self.database_url,
            'pool_size': self.database_pool_size,
            'max_overflow': self.database_max_overflow,
            'echo': self.database_echo,
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dict"""
        return {
            'url': self.redis_url,
            'cache_url': self.redis_cache_url,
            'max_connections': self.redis_max_connections,
        }
    
    def get_celery_config(self) -> Dict[str, Any]:
        """Get Celery configuration dict"""
        return {
            'broker_url': self.celery_broker_url,
            'result_backend': self.celery_result_backend,
            'task_timeout': self.celery_task_timeout,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Development settings override
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    database_echo: bool = True
    api_docs_enabled: bool = True


# Production settings override
class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "WARNING"
    database_echo: bool = False
    api_docs_enabled: bool = False
    
    class Config:
        env_file = ".env.production"


# Testing settings override
class TestingSettings(Settings):
    """Testing environment settings"""
    environment: Environment = Environment.TESTING
    debug: bool = True
    database_url: str = "postgresql://test:test@localhost:5432/test_emydb"
    redis_url: str = "redis://localhost:6379/15"


def get_environment_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return ProductionSettings()
    elif env == 'testing':
        return TestingSettings()
    else:
        return DevelopmentSettings()
