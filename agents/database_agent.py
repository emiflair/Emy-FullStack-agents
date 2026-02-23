"""
Database Engineer / Data Specialist Agent
Responsible for designing PostgreSQL/Redis schema, storing campaign logs,
analytics, content history, and maintaining data integrity.
"""

from typing import Any, Dict, List
from .base_agent import BaseAgent, Task


class DatabaseAgent(BaseAgent):
    """
    Database Engineer Agent for the Emy-FullStack system.
    
    Capabilities:
    - Design PostgreSQL / Redis schema
    - Store campaign logs, analytics, content history
    - Maintain integrity and backups
    - Create migrations
    - Optimize queries
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="Database Engineer",
            description="Designs and manages database schemas and data operations",
            capabilities=[
                "schema_design",
                "migrations",
                "query_optimization",
                "caching",
                "backup",
                "analytics",
            ],
            config=config or {}
        )
        self.db_type = config.get("db_type", "postgresql") if config else "postgresql"
        self.generated_schemas: List[str] = []
        self.generated_migrations: List[str] = []

    async def execute_task(self, task: Task) -> Any:
        """Execute a database engineering task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "schema_design": self._design_schema,
            "migrations": self._create_migration,
            "query_optimization": self._optimize_queries,
            "caching": self._setup_caching,
            "backup": self._setup_backup,
            "analytics": self._setup_analytics,
            "create_tables": self._create_tables,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _design_schema(self, task: Task) -> Dict[str, Any]:
        """Design database schema."""
        tables = task.metadata.get("tables", [])
        relationships = task.metadata.get("relationships", [])
        
        self.log(f"Designing schema with {len(tables)} tables")
        
        schema_code = self._generate_schema_code(tables, relationships)
        
        return {
            "tables": tables,
            "relationships": relationships,
            "code": schema_code,
        }

    def _generate_schema_code(self, tables: List[Dict], relationships: List[Dict]) -> str:
        """Generate SQLAlchemy models for schema."""
        code = '''from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

'''
        for table in tables:
            table_name = table.get("name", "table")
            fields = table.get("fields", [])
            
            code += f'''
class {table_name.title()}(Base):
    __tablename__ = "{table_name.lower()}s"
    
    id = Column(Integer, primary_key=True, index=True)
'''
            for field in fields:
                field_name = field.get("name", "field")
                field_type = self._get_sqlalchemy_type(field.get("type", "string"))
                nullable = field.get("nullable", True)
                default = field.get("default")
                
                default_str = f", default={default}" if default else ""
                nullable_str = f", nullable={nullable}"
                
                code += f"    {field_name} = Column({field_type}{nullable_str}{default_str})\n"
            
            code += '''    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

'''
        return code

    def _get_sqlalchemy_type(self, field_type: str) -> str:
        """Convert field type to SQLAlchemy type."""
        type_mapping = {
            "string": "String(255)",
            "text": "Text",
            "integer": "Integer",
            "float": "Float",
            "boolean": "Boolean",
            "datetime": "DateTime",
            "json": "JSON",
        }
        return type_mapping.get(field_type.lower(), "String(255)")

    async def _create_tables(self, task: Task) -> Dict[str, Any]:
        """Create database tables."""
        tables = task.metadata.get("tables", ["sellers", "campaigns", "content_logs"])
        
        self.log(f"Creating tables: {tables}")
        
        sql_code = self._generate_create_tables_sql(tables)
        model_code = self._generate_models_code(tables)
        
        self.generated_schemas.extend(tables)
        
        return {
            "tables": tables,
            "sql": sql_code,
            "models": model_code,
        }

    def _generate_create_tables_sql(self, tables: List[str]) -> str:
        """Generate SQL CREATE TABLE statements."""
        sql = "-- Database Schema for Emy-FullStack\n\n"
        
        if "sellers" in tables:
            sql += '''-- Sellers table
CREATE TABLE IF NOT EXISTS sellers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    country VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sellers_email ON sellers(email);
CREATE INDEX idx_sellers_country ON sellers(country);

'''
        
        if "campaigns" in tables:
            sql += '''-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER REFERENCES sellers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    target_audience JSONB DEFAULT '{}',
    budget DECIMAL(12, 2),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaigns_seller ON campaigns(seller_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);

'''
        
        if "content_logs" in tables:
            sql += '''-- Content Logs table
CREATE TABLE IF NOT EXISTS content_logs (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    content_type VARCHAR(100) NOT NULL,
    content TEXT,
    platform VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    engagement_metrics JSONB DEFAULT '{}',
    error_log TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_content_logs_campaign ON content_logs(campaign_id);
CREATE INDEX idx_content_logs_platform ON content_logs(platform);
CREATE INDEX idx_content_logs_status ON content_logs(status);

'''
        
        return sql

    def _generate_models_code(self, tables: List[str]) -> str:
        """Generate SQLAlchemy model code."""
        code = '''"""
Database models for Emy-FullStack
Auto-generated by Database Agent
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

'''
        if "sellers" in tables:
            code += '''
class Seller(Base):
    __tablename__ = "sellers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    company = Column(String(255))
    country = Column(String(100), index=True)
    status = Column(String(50), default="active")
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="seller", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "country": self.country,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

'''
        
        if "campaigns" in tables:
            code += '''
class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="CASCADE"), index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    campaign_type = Column(String(100))
    status = Column(String(50), default="draft", index=True)
    target_audience = Column(JSONB, default={})
    budget = Column(Numeric(12, 2))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("Seller", back_populates="campaigns")
    content_logs = relationship("ContentLog", back_populates="campaign", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "name": self.name,
            "description": self.description,
            "campaign_type": self.campaign_type,
            "status": self.status,
            "budget": float(self.budget) if self.budget else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

'''
        
        if "content_logs" in tables:
            code += '''
class ContentLog(Base):
    __tablename__ = "content_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    content_type = Column(String(100), nullable=False)
    content = Column(Text)
    platform = Column(String(100), index=True)
    status = Column(String(50), default="pending", index=True)
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)
    engagement_metrics = Column(JSONB, default={})
    error_log = Column(Text)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="content_logs")
    
    def to_dict(self):
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "content_type": self.content_type,
            "platform": self.platform,
            "status": self.status,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "engagement_metrics": self.engagement_metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

'''
        
        return code

    async def _create_migration(self, task: Task) -> Dict[str, Any]:
        """Create database migration."""
        migration_name = task.metadata.get("name", "migration")
        changes = task.metadata.get("changes", [])
        
        self.log(f"Creating migration: {migration_name}")
        
        migration_code = self._generate_migration_code(migration_name, changes)
        
        self.generated_migrations.append(migration_name)
        
        return {
            "name": migration_name,
            "changes": changes,
            "code": migration_code,
        }

    def _generate_migration_code(self, name: str, changes: List[Dict]) -> str:
        """Generate Alembic migration code."""
        return f'''"""
{name}

Revision ID: auto_generated
Create Date: {{datetime.now().isoformat()}}
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'auto_generated'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add migration upgrade operations here
    pass

def downgrade():
    # Add migration downgrade operations here
    pass
'''

    async def _optimize_queries(self, task: Task) -> Dict[str, Any]:
        """Optimize database queries."""
        queries = task.metadata.get("queries", [])
        
        self.log(f"Optimizing {len(queries)} queries")
        
        return {
            "original_queries": queries,
            "optimizations": self._analyze_queries(queries),
            "recommendations": [
                "Add indexes on frequently queried columns",
                "Use EXPLAIN ANALYZE to check query plans",
                "Consider query caching for repeated queries",
                "Batch inserts/updates for better performance",
            ],
        }

    def _analyze_queries(self, queries: List[str]) -> List[Dict]:
        """Analyze queries for optimization."""
        optimizations = []
        for query in queries:
            opt = {
                "original": query,
                "suggestions": [],
            }
            if "SELECT *" in query.upper():
                opt["suggestions"].append("Specify columns instead of SELECT *")
            if "WHERE" not in query.upper():
                opt["suggestions"].append("Consider adding WHERE clause")
            optimizations.append(opt)
        return optimizations

    async def _setup_caching(self, task: Task) -> Dict[str, Any]:
        """Setup Redis caching."""
        cache_strategy = task.metadata.get("strategy", "read-through")
        ttl = task.metadata.get("ttl", 3600)
        
        self.log(f"Setting up caching: {cache_strategy}")
        
        cache_code = self._generate_cache_code(cache_strategy, ttl)
        
        return {
            "strategy": cache_strategy,
            "ttl": ttl,
            "code": cache_code,
        }

    def _generate_cache_code(self, strategy: str, ttl: int) -> str:
        """Generate Redis caching code."""
        return f'''import redis
import json
from typing import Any, Optional, Callable
from functools import wraps

# Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

DEFAULT_TTL = {ttl}

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{{k}}={{v}}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)

def cache(ttl: int = DEFAULT_TTL, prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{{prefix}}:{{func.__name__}}:{{cache_key(*args, **kwargs)}}"
            
            # Try to get from cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate cache keys matching pattern."""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

def get_cached(key: str) -> Optional[Any]:
    """Get cached value."""
    cached = redis_client.get(key)
    return json.loads(cached) if cached else None

def set_cached(key: str, value: Any, ttl: int = DEFAULT_TTL):
    """Set cached value."""
    redis_client.setex(key, ttl, json.dumps(value))

# Usage example:
# @cache(ttl=300, prefix="api")
# async def get_user(user_id: int):
#     return await db.query(User).filter(User.id == user_id).first()
'''

    async def _setup_backup(self, task: Task) -> Dict[str, Any]:
        """Setup database backup strategy."""
        backup_type = task.metadata.get("type", "full")
        schedule = task.metadata.get("schedule", "daily")
        
        self.log(f"Setting up {backup_type} backup: {schedule}")
        
        backup_script = self._generate_backup_script(backup_type, schedule)
        
        return {
            "type": backup_type,
            "schedule": schedule,
            "script": backup_script,
        }

    def _generate_backup_script(self, backup_type: str, schedule: str) -> str:
        """Generate backup script."""
        return '''#!/bin/bash
# Database Backup Script

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-emy_fullstack}"
DB_USER="${DB_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS=7

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz"

# Perform backup
echo "Starting backup: $BACKUP_FILE"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Clean old backups
    find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Cleaned backups older than $RETENTION_DAYS days"
else
    echo "Backup failed!"
    exit 1
fi
'''

    async def _setup_analytics(self, task: Task) -> Dict[str, Any]:
        """Setup analytics tables and queries."""
        metrics = task.metadata.get("metrics", ["views", "clicks", "conversions"])
        
        self.log(f"Setting up analytics for: {metrics}")
        
        analytics_code = self._generate_analytics_code(metrics)
        
        return {
            "metrics": metrics,
            "code": analytics_code,
        }

    def _generate_analytics_code(self, metrics: List[str]) -> str:
        """Generate analytics code."""
        return '''-- Analytics Schema

CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    user_id INTEGER,
    session_id VARCHAR(255),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_entity ON analytics_events(entity_type, entity_id);
CREATE INDEX idx_analytics_created ON analytics_events(created_at);

-- Aggregated daily stats
CREATE TABLE IF NOT EXISTS analytics_daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(12, 2) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, entity_type, entity_id)
);

CREATE INDEX idx_daily_stats_date ON analytics_daily_stats(date);

-- Analytics queries
-- Daily summary
SELECT 
    date,
    SUM(views) as total_views,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions,
    SUM(revenue) as total_revenue
FROM analytics_daily_stats
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date
ORDER BY date DESC;

-- Top performing entities
SELECT 
    entity_type,
    entity_id,
    SUM(views) as total_views,
    SUM(clicks) as total_clicks,
    CASE WHEN SUM(views) > 0 
         THEN ROUND(SUM(clicks)::numeric / SUM(views) * 100, 2) 
         ELSE 0 
    END as ctr
FROM analytics_daily_stats
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY entity_type, entity_id
ORDER BY total_views DESC
LIMIT 10;
'''

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic database tasks."""
        self.log(f"Handling generic database task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic database task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with database-specific info."""
        base_status = super().get_status()
        base_status.update({
            "db_type": self.db_type,
            "generated_schemas": self.generated_schemas,
            "generated_migrations": self.generated_migrations,
        })
        return base_status
