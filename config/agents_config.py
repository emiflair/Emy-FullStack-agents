"""
Agents Configuration
Settings for all AI agents
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class AgentType(str, Enum):
    """Agent types"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    QA = "qa"
    UIUX = "uiux"
    SECURITY = "security"
    AIML = "aiml"
    PROJECT_MANAGER = "project_manager"


class AgentPriority(int, Enum):
    """Agent priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 7
    CRITICAL = 10


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    agent_type: AgentType
    name: str
    enabled: bool = True
    priority: AgentPriority = AgentPriority.NORMAL
    
    # Execution settings
    concurrency: int = 2
    max_tasks: int = 100
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 60  # seconds
    
    # Queue settings
    queue_name: Optional[str] = None
    prefetch_count: int = 4
    
    # Rate limiting
    rate_limit: Optional[str] = None  # e.g., "100/m" for 100 per minute
    
    # Dependencies
    depends_on: List[AgentType] = field(default_factory=list)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.queue_name:
            self.queue_name = self.agent_type.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.agent_type.value,
            'name': self.name,
            'enabled': self.enabled,
            'priority': self.priority.value,
            'concurrency': self.concurrency,
            'max_tasks': self.max_tasks,
            'timeout': self.timeout,
            'queue_name': self.queue_name,
            'rate_limit': self.rate_limit,
        }


@dataclass
class AgentsConfig:
    """Configuration for all agents"""
    agents: Dict[AgentType, AgentConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        # Initialize default agent configurations
        if not self.agents:
            self.agents = self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[AgentType, AgentConfig]:
        return {
            AgentType.FRONTEND: AgentConfig(
                agent_type=AgentType.FRONTEND,
                name="Frontend Agent",
                priority=AgentPriority.NORMAL,
                concurrency=2,
                timeout=300,
                custom_settings={
                    'framework': 'flutter',
                    'state_management': 'riverpod',
                    'supported_platforms': ['ios', 'android', 'web'],
                },
            ),
            AgentType.BACKEND: AgentConfig(
                agent_type=AgentType.BACKEND,
                name="Backend Agent",
                priority=AgentPriority.HIGH,
                concurrency=4,
                timeout=600,
                depends_on=[AgentType.DATABASE],
                custom_settings={
                    'framework': 'fastapi',
                    'auth': 'jwt',
                    'api_prefix': '/api/v1',
                },
            ),
            AgentType.DATABASE: AgentConfig(
                agent_type=AgentType.DATABASE,
                name="Database Agent",
                priority=AgentPriority.HIGH,
                concurrency=2,
                timeout=600,
                rate_limit='50/m',
                custom_settings={
                    'primary_db': 'postgresql',
                    'cache_db': 'redis',
                    'orm': 'sqlalchemy',
                },
            ),
            AgentType.DEVOPS: AgentConfig(
                agent_type=AgentType.DEVOPS,
                name="DevOps Agent",
                priority=AgentPriority.NORMAL,
                concurrency=2,
                timeout=900,
                depends_on=[AgentType.BACKEND, AgentType.FRONTEND],
                custom_settings={
                    'container_runtime': 'docker',
                    'orchestration': 'kubernetes',
                    'ci_cd': 'github_actions',
                    'cloud_providers': ['aws', 'gcp'],
                },
            ),
            AgentType.QA: AgentConfig(
                agent_type=AgentType.QA,
                name="QA Agent",
                priority=AgentPriority.NORMAL,
                concurrency=3,
                timeout=600,
                depends_on=[AgentType.BACKEND, AgentType.FRONTEND],
                custom_settings={
                    'testing_frameworks': ['pytest', 'flutter_test'],
                    'coverage_threshold': 80,
                    'test_types': ['unit', 'integration', 'e2e'],
                },
            ),
            AgentType.UIUX: AgentConfig(
                agent_type=AgentType.UIUX,
                name="UI/UX Agent",
                priority=AgentPriority.NORMAL,
                concurrency=2,
                timeout=300,
                custom_settings={
                    'design_system': 'material',
                    'responsive_breakpoints': [320, 768, 1024, 1440],
                    'accessibility_level': 'AA',
                },
            ),
            AgentType.SECURITY: AgentConfig(
                agent_type=AgentType.SECURITY,
                name="Security Agent",
                priority=AgentPriority.CRITICAL,
                concurrency=2,
                timeout=600,
                custom_settings={
                    'encryption': 'aes-256',
                    'auth_method': 'oauth2',
                    'scan_frequency': 'daily',
                    'compliance': ['owasp', 'gdpr'],
                },
            ),
            AgentType.AIML: AgentConfig(
                agent_type=AgentType.AIML,
                name="AI/ML Agent",
                priority=AgentPriority.HIGH,
                concurrency=2,
                timeout=1200,
                custom_settings={
                    'llm_provider': 'openai',
                    'default_model': 'gpt-4',
                    'embedding_model': 'text-embedding-ada-002',
                    'max_tokens': 2000,
                },
            ),
            AgentType.PROJECT_MANAGER: AgentConfig(
                agent_type=AgentType.PROJECT_MANAGER,
                name="Project Manager Agent",
                priority=AgentPriority.HIGH,
                concurrency=1,
                timeout=300,
                custom_settings={
                    'sprint_duration': 14,  # days
                    'max_concurrent_projects': 5,
                    'task_estimation_method': 'story_points',
                },
            ),
        }
    
    def get_agent(self, agent_type: AgentType) -> Optional[AgentConfig]:
        """Get agent configuration"""
        return self.agents.get(agent_type)
    
    def get_enabled_agents(self) -> List[AgentConfig]:
        """Get all enabled agents"""
        return [agent for agent in self.agents.values() if agent.enabled]
    
    def get_agents_by_priority(self, min_priority: AgentPriority) -> List[AgentConfig]:
        """Get agents with priority >= min_priority"""
        return [
            agent for agent in self.agents.values()
            if agent.priority.value >= min_priority.value
        ]
    
    def update_agent(self, agent_type: AgentType, **updates) -> Optional[AgentConfig]:
        """Update agent configuration"""
        agent = self.agents.get(agent_type)
        if agent:
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
        return agent
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            agent_type.value: config.to_dict()
            for agent_type, config in self.agents.items()
        }


# Task capability mapping
AGENT_CAPABILITIES = {
    AgentType.FRONTEND: [
        'generate_ui',
        'create_widget',
        'implement_state',
        'add_animation',
        'responsive_layout',
        'api_integration',
    ],
    AgentType.BACKEND: [
        'create_endpoint',
        'implement_crud',
        'add_authentication',
        'create_middleware',
        'database_integration',
        'api_documentation',
    ],
    AgentType.DATABASE: [
        'design_schema',
        'create_migration',
        'optimize_query',
        'setup_caching',
        'create_backup',
        'data_modeling',
    ],
    AgentType.DEVOPS: [
        'create_dockerfile',
        'setup_kubernetes',
        'configure_ci_cd',
        'setup_monitoring',
        'infrastructure_as_code',
        'deployment',
    ],
    AgentType.QA: [
        'write_unit_tests',
        'write_integration_tests',
        'write_e2e_tests',
        'generate_coverage',
        'performance_testing',
        'security_testing',
    ],
    AgentType.UIUX: [
        'create_wireframe',
        'design_layout',
        'create_design_system',
        'accessibility_audit',
        'user_flow',
        'prototype',
    ],
    AgentType.SECURITY: [
        'vulnerability_scan',
        'implement_auth',
        'encrypt_data',
        'setup_rbac',
        'audit_logging',
        'compliance_check',
    ],
    AgentType.AIML: [
        'generate_content',
        'train_model',
        'predict',
        'analyze_data',
        'optimize_recommendations',
        'nlp_processing',
    ],
    AgentType.PROJECT_MANAGER: [
        'plan_sprint',
        'assign_tasks',
        'track_progress',
        'generate_report',
        'manage_dependencies',
        'risk_assessment',
    ],
}


def get_agents_config() -> AgentsConfig:
    """Get agents configuration"""
    return AgentsConfig()
