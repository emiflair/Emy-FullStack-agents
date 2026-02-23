"""
AI-Powered Agent Mixin
Adds AI code generation capabilities to agents
"""

import asyncio
from typing import Any, Dict, List, Optional
import os

from core.ai_generator import (
    AICodeGenerator, 
    CodeGenerationRequest, 
    GenerationType, 
    CodeLanguage,
    GeneratedCode,
)


class AIEnabledMixin:
    """
    Mixin that adds AI code generation capabilities to agents.
    
    Usage:
        class MyAgent(AIEnabledMixin, BaseAgent):
            pass
    """
    
    _ai_generator: Optional[AICodeGenerator] = None
    
    @property
    def ai_generator(self) -> AICodeGenerator:
        """Get or create the AI code generator"""
        if self._ai_generator is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._ai_generator = AICodeGenerator(api_key=api_key)
            else:
                raise ValueError("OPENAI_API_KEY not configured")
        return self._ai_generator
    
    def has_ai(self) -> bool:
        """Check if AI generation is available"""
        return bool(os.getenv("OPENAI_API_KEY"))
    
    async def generate_code(
        self,
        generation_type: GenerationType,
        description: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        requirements: List[str] = None,
        constraints: List[str] = None,
        context: Dict[str, Any] = None,
    ) -> GeneratedCode:
        """
        Generate code using AI.
        
        Args:
            generation_type: Type of code to generate
            description: What to generate
            language: Programming language
            requirements: List of requirements
            constraints: List of constraints
            context: Additional context
            
        Returns:
            GeneratedCode object
        """
        request = CodeGenerationRequest(
            generation_type=generation_type,
            description=description,
            language=language,
            requirements=requirements or [],
            constraints=constraints or [],
            context=context or {},
        )
        
        return await self.ai_generator.generate(request)
    
    def generate_code_sync(
        self,
        generation_type: GenerationType,
        description: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        requirements: List[str] = None,
        constraints: List[str] = None,
        context: Dict[str, Any] = None,
    ) -> GeneratedCode:
        """Synchronous version of generate_code"""
        request = CodeGenerationRequest(
            generation_type=generation_type,
            description=description,
            language=language,
            requirements=requirements or [],
            constraints=constraints or [],
            context=context or {},
        )
        
        return self.ai_generator.generate_sync(request)
    
    # Convenience methods for Flutter (Frontend Agent)
    
    async def generate_flutter_widget(
        self,
        widget_name: str,
        description: str,
        properties: List[str] = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate a Flutter widget"""
        desc = f"Flutter widget '{widget_name}': {description}"
        if properties:
            desc += f"\nProperties: {', '.join(properties)}"
        
        return await self.generate_code(
            generation_type=GenerationType.FLUTTER_WIDGET,
            description=desc,
            language=CodeLanguage.DART,
            **kwargs
        )
    
    async def generate_flutter_screen(
        self,
        screen_name: str,
        description: str,
        components: List[str] = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate a Flutter screen"""
        desc = f"Flutter screen '{screen_name}': {description}"
        if components:
            desc += f"\nComponents: {', '.join(components)}"
        
        return await self.generate_code(
            generation_type=GenerationType.FLUTTER_SCREEN,
            description=desc,
            language=CodeLanguage.DART,
            **kwargs
        )
    
    async def generate_flutter_service(
        self,
        service_name: str,
        description: str,
        methods: List[str] = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate a Flutter service"""
        desc = f"Flutter service '{service_name}': {description}"
        if methods:
            desc += f"\nMethods: {', '.join(methods)}"
        
        return await self.generate_code(
            generation_type=GenerationType.FLUTTER_SERVICE,
            description=desc,
            language=CodeLanguage.DART,
            **kwargs
        )
    
    # Convenience methods for FastAPI (Backend Agent)
    
    async def generate_api_endpoint(
        self,
        endpoint_path: str,
        method: str,
        description: str,
        request_model: str = None,
        response_model: str = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate a FastAPI endpoint"""
        desc = f"FastAPI {method} endpoint '{endpoint_path}': {description}"
        if request_model:
            desc += f"\nRequest model: {request_model}"
        if response_model:
            desc += f"\nResponse model: {response_model}"
        
        return await self.generate_code(
            generation_type=GenerationType.FASTAPI_ENDPOINT,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    async def generate_api_model(
        self,
        model_name: str,
        fields: Dict[str, str],
        **kwargs
    ) -> GeneratedCode:
        """Generate a Pydantic model"""
        desc = f"Pydantic model '{model_name}'"
        desc += f"\nFields: {fields}"
        
        return await self.generate_code(
            generation_type=GenerationType.FASTAPI_MODEL,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    async def generate_api_service(
        self,
        service_name: str,
        description: str,
        methods: List[str] = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate a FastAPI service class"""
        desc = f"FastAPI service '{service_name}': {description}"
        if methods:
            desc += f"\nMethods: {', '.join(methods)}"
        
        return await self.generate_code(
            generation_type=GenerationType.FASTAPI_SERVICE,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    # Convenience methods for Database
    
    async def generate_database_model(
        self,
        model_name: str,
        fields: Dict[str, str],
        relationships: List[str] = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate a SQLAlchemy model"""
        desc = f"SQLAlchemy model '{model_name}'"
        desc += f"\nFields: {fields}"
        if relationships:
            desc += f"\nRelationships: {', '.join(relationships)}"
        
        return await self.generate_code(
            generation_type=GenerationType.DATABASE_SCHEMA,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    async def generate_migration(
        self,
        description: str,
        changes: List[str],
        **kwargs
    ) -> GeneratedCode:
        """Generate an Alembic migration"""
        desc = f"Alembic migration: {description}"
        desc += f"\nChanges: {', '.join(changes)}"
        
        return await self.generate_code(
            generation_type=GenerationType.DATABASE_MIGRATION,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    # Convenience methods for DevOps
    
    async def generate_dockerfile(
        self,
        app_type: str,
        description: str,
        **kwargs
    ) -> GeneratedCode:
        """Generate a Dockerfile"""
        desc = f"Dockerfile for {app_type}: {description}"
        
        return await self.generate_code(
            generation_type=GenerationType.DOCKER_CONFIG,
            description=desc,
            language=CodeLanguage.DOCKERFILE,
            **kwargs
        )
    
    async def generate_kubernetes_manifest(
        self,
        resource_type: str,
        name: str,
        description: str,
        **kwargs
    ) -> GeneratedCode:
        """Generate Kubernetes manifest"""
        desc = f"Kubernetes {resource_type} '{name}': {description}"
        
        return await self.generate_code(
            generation_type=GenerationType.KUBERNETES_MANIFEST,
            description=desc,
            language=CodeLanguage.YAML,
            **kwargs
        )
    
    # Convenience methods for Testing
    
    async def generate_unit_test(
        self,
        target: str,
        test_cases: List[str],
        **kwargs
    ) -> GeneratedCode:
        """Generate unit tests"""
        desc = f"Unit tests for '{target}'"
        desc += f"\nTest cases: {', '.join(test_cases)}"
        
        return await self.generate_code(
            generation_type=GenerationType.TEST_UNIT,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    async def generate_integration_test(
        self,
        target: str,
        scenarios: List[str],
        **kwargs
    ) -> GeneratedCode:
        """Generate integration tests"""
        desc = f"Integration tests for '{target}'"
        desc += f"\nScenarios: {', '.join(scenarios)}"
        
        return await self.generate_code(
            generation_type=GenerationType.TEST_INTEGRATION,
            description=desc,
            language=CodeLanguage.PYTHON,
            **kwargs
        )
    
    # Documentation
    
    async def generate_documentation(
        self,
        doc_type: str,
        subject: str,
        sections: List[str] = None,
        **kwargs
    ) -> GeneratedCode:
        """Generate documentation"""
        desc = f"{doc_type} documentation for '{subject}'"
        if sections:
            desc += f"\nSections: {', '.join(sections)}"
        
        return await self.generate_code(
            generation_type=GenerationType.DOCUMENTATION,
            description=desc,
            language=CodeLanguage.MARKDOWN,
            **kwargs
        )
