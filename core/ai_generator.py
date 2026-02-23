"""
AI Code Generator
Connects to OpenAI GPT-4 for intelligent code generation
"""

import os
import json
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import logging

try:
    import openai
    from openai import AsyncOpenAI, OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)


class CodeLanguage(Enum):
    """Supported code languages"""
    DART = "dart"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SQL = "sql"
    YAML = "yaml"
    DOCKERFILE = "dockerfile"
    SHELL = "shell"
    JSON = "json"
    MARKDOWN = "markdown"


class GenerationType(Enum):
    """Types of code generation"""
    FLUTTER_WIDGET = "flutter_widget"
    FLUTTER_SCREEN = "flutter_screen"
    FLUTTER_SERVICE = "flutter_service"
    FASTAPI_ENDPOINT = "fastapi_endpoint"
    FASTAPI_MODEL = "fastapi_model"
    FASTAPI_SERVICE = "fastapi_service"
    DATABASE_SCHEMA = "database_schema"
    DATABASE_MIGRATION = "database_migration"
    DOCKER_CONFIG = "docker_config"
    KUBERNETES_MANIFEST = "kubernetes_manifest"
    TEST_UNIT = "test_unit"
    TEST_INTEGRATION = "test_integration"
    DOCUMENTATION = "documentation"
    GENERIC = "generic"


@dataclass
class CodeGenerationRequest:
    """Request for code generation"""
    generation_type: GenerationType
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    language: CodeLanguage = CodeLanguage.PYTHON
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    existing_code: Optional[str] = None  # For modifications/enhancements
    project_context: Optional[str] = None  # Project-level context
    max_tokens: int = 4000
    temperature: float = 0.2  # Lower for more deterministic code


@dataclass
class GeneratedCode:
    """Result of code generation"""
    code: str
    language: CodeLanguage
    filename: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    tests_suggested: List[str] = field(default_factory=list)
    documentation: str = ""
    confidence_score: float = 0.0
    generation_time: float = 0.0
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'language': self.language.value,
            'filename': self.filename,
            'description': self.description,
            'dependencies': self.dependencies,
            'tests_suggested': self.tests_suggested,
            'documentation': self.documentation,
            'confidence_score': self.confidence_score,
        }


class AICodeGenerator:
    """
    AI-powered code generator using OpenAI GPT-4
    Generates production-ready code for various frameworks
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client: Optional[AsyncOpenAI] = None
        self._sync_client: Optional[OpenAI] = None
        
        # System prompts for different generation types
        self._system_prompts = self._build_system_prompts()
        
        # Generation history for learning
        self._generation_history: List[Dict[str, Any]] = []
    
    def _build_system_prompts(self) -> Dict[GenerationType, str]:
        """Build specialized system prompts for each generation type"""
        base_prompt = """You are an expert senior software engineer specializing in building 
production-ready applications. Generate clean, well-documented, and tested code.
Always follow best practices and modern patterns."""

        return {
            GenerationType.FLUTTER_WIDGET: f"""{base_prompt}

You are a Flutter/Dart expert. Generate Flutter widgets that:
- Follow Flutter best practices and material design guidelines
- Use proper state management (Riverpod/Provider patterns)
- Include proper widget lifecycle handling
- Are responsive and accessible
- Include inline documentation""",

            GenerationType.FLUTTER_SCREEN: f"""{base_prompt}

You are a Flutter/Dart expert. Generate complete Flutter screens that:
- Include proper navigation integration
- Handle loading, error, and empty states
- Use responsive layouts
- Include proper state management
- Follow clean architecture principles""",

            GenerationType.FLUTTER_SERVICE: f"""{base_prompt}

You are a Flutter/Dart expert. Generate Flutter services that:
- Handle API communication with proper error handling
- Include retry logic and timeout handling
- Use proper async patterns
- Include caching where appropriate
- Are easily testable""",

            GenerationType.FASTAPI_ENDPOINT: f"""{base_prompt}

You are a FastAPI/Python expert. Generate FastAPI endpoints that:
- Include proper request/response models with Pydantic
- Have comprehensive error handling
- Include OpenAPI documentation
- Follow RESTful conventions
- Include authentication/authorization decorators
- Are async when appropriate""",

            GenerationType.FASTAPI_MODEL: f"""{base_prompt}

You are a FastAPI/Python expert. Generate Pydantic models that:
- Include proper validation
- Have field descriptions for documentation
- Include sensible defaults
- Support serialization/deserialization
- Handle optional fields appropriately""",

            GenerationType.FASTAPI_SERVICE: f"""{base_prompt}

You are a FastAPI/Python expert. Generate service classes that:
- Follow dependency injection patterns
- Are easily testable
- Include proper logging
- Handle database transactions
- Include proper error handling""",

            GenerationType.DATABASE_SCHEMA: f"""{base_prompt}

You are a database expert. Generate SQLAlchemy models that:
- Include proper relationships and foreign keys
- Have appropriate indexes
- Include created_at/updated_at timestamps
- Follow naming conventions
- Include proper constraints""",

            GenerationType.DATABASE_MIGRATION: f"""{base_prompt}

You are a database expert. Generate Alembic migrations that:
- Are reversible (include downgrade)
- Handle data migrations safely
- Include proper transaction handling
- Have descriptive revision messages""",

            GenerationType.DOCKER_CONFIG: f"""{base_prompt}

You are a DevOps expert. Generate Docker configurations that:
- Use multi-stage builds for optimization
- Follow security best practices
- Include health checks
- Use proper base images
- Include proper environment handling""",

            GenerationType.KUBERNETES_MANIFEST: f"""{base_prompt}

You are a Kubernetes expert. Generate K8s manifests that:
- Include proper resource limits
- Use proper labels and selectors
- Include health checks and probes
- Follow security best practices
- Are production-ready""",

            GenerationType.TEST_UNIT: f"""{base_prompt}

You are a testing expert. Generate unit tests that:
- Cover edge cases
- Use proper mocking
- Follow AAA pattern (Arrange, Act, Assert)
- Are independent and isolated
- Include descriptive test names""",

            GenerationType.TEST_INTEGRATION: f"""{base_prompt}

You are a testing expert. Generate integration tests that:
- Test real interactions between components
- Handle proper setup and teardown
- Use test databases/fixtures
- Include proper assertions
- Are reliable and not flaky""",

            GenerationType.DOCUMENTATION: f"""{base_prompt}

You are a technical writer. Generate documentation that:
- Is clear and comprehensive
- Includes code examples
- Follows standard formats (README, API docs)
- Is easy to maintain
- Includes relevant diagrams/references""",

            GenerationType.GENERIC: base_prompt,
        }
    
    async def _get_client(self) -> AsyncOpenAI:
        """Get or create async OpenAI client"""
        if not HAS_OPENAI:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    def _get_sync_client(self) -> OpenAI:
        """Get or create sync OpenAI client"""
        if not HAS_OPENAI:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        if self._sync_client is None:
            self._sync_client = OpenAI(api_key=self.api_key)
        return self._sync_client
    
    def _build_prompt(self, request: CodeGenerationRequest) -> str:
        """Build the user prompt for code generation"""
        prompt_parts = [
            f"Generate {request.generation_type.value.replace('_', ' ')} code.",
            f"\nDescription: {request.description}",
        ]
        
        if request.requirements:
            prompt_parts.append(f"\nRequirements:\n- " + "\n- ".join(request.requirements))
        
        if request.constraints:
            prompt_parts.append(f"\nConstraints:\n- " + "\n- ".join(request.constraints))
        
        if request.context:
            prompt_parts.append(f"\nContext: {json.dumps(request.context, indent=2)}")
        
        if request.project_context:
            prompt_parts.append(f"\nProject Context:\n{request.project_context}")
        
        if request.existing_code:
            prompt_parts.append(f"\nExisting code to enhance/modify:\n```{request.language.value}\n{request.existing_code}\n```")
        
        prompt_parts.append(f"\nRespond with ONLY the code, no explanations. Start with the code block.")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(
        self, 
        response_text: str, 
        request: CodeGenerationRequest
    ) -> GeneratedCode:
        """Parse AI response into GeneratedCode object"""
        # Extract code from markdown code blocks if present
        code = response_text.strip()
        
        # Remove markdown code fences if present
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line (```language)
            lines = lines[1:]
            # Remove last line if it's just ``````
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        # Generate appropriate filename
        filename = self._generate_filename(request)
        
        # Detect dependencies from code
        dependencies = self._detect_dependencies(code, request.language)
        
        return GeneratedCode(
            code=code,
            language=request.language,
            filename=filename,
            description=request.description,
            dependencies=dependencies,
            tests_suggested=self._suggest_tests(request),
        )
    
    def _generate_filename(self, request: CodeGenerationRequest) -> str:
        """Generate appropriate filename based on generation type"""
        type_to_extension = {
            CodeLanguage.DART: ".dart",
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.JAVASCRIPT: ".js",
            CodeLanguage.TYPESCRIPT: ".ts",
            CodeLanguage.SQL: ".sql",
            CodeLanguage.YAML: ".yaml",
            CodeLanguage.DOCKERFILE: "",
            CodeLanguage.SHELL: ".sh",
            CodeLanguage.JSON: ".json",
            CodeLanguage.MARKDOWN: ".md",
        }
        
        # Generate name from description
        name = request.description.lower()
        name = "".join(c if c.isalnum() or c == " " else "" for c in name)
        name = "_".join(name.split()[:3])  # First 3 words
        
        ext = type_to_extension.get(request.language, ".txt")
        
        if request.generation_type == GenerationType.DOCKERFILE:
            return "Dockerfile"
        
        return f"{name}{ext}"
    
    def _detect_dependencies(self, code: str, language: CodeLanguage) -> List[str]:
        """Detect dependencies from generated code"""
        dependencies = []
        
        if language == CodeLanguage.PYTHON:
            # Look for imports
            for line in code.split("\n"):
                if line.startswith("import ") or line.startswith("from "):
                    parts = line.split()
                    if len(parts) >= 2:
                        module = parts[1].split(".")[0]
                        if module not in ["os", "sys", "json", "typing", "dataclasses", "enum", "datetime"]:
                            dependencies.append(module)
        
        elif language == CodeLanguage.DART:
            # Look for package imports
            for line in code.split("\n"):
                if line.startswith("import 'package:"):
                    package = line.split(":")[1].split("/")[0]
                    dependencies.append(package)
        
        return list(set(dependencies))
    
    def _suggest_tests(self, request: CodeGenerationRequest) -> List[str]:
        """Suggest tests for the generated code"""
        suggestions = []
        
        if request.generation_type in [GenerationType.FLUTTER_WIDGET, GenerationType.FLUTTER_SCREEN]:
            suggestions.extend([
                "Widget renders correctly",
                "Handles loading state",
                "Handles error state",
                "User interactions work",
            ])
        
        elif request.generation_type == GenerationType.FASTAPI_ENDPOINT:
            suggestions.extend([
                "Returns correct status codes",
                "Validates input correctly",
                "Handles authentication",
                "Returns proper error messages",
            ])
        
        elif request.generation_type == GenerationType.DATABASE_SCHEMA:
            suggestions.extend([
                "Model creates correctly",
                "Relationships work",
                "Constraints are enforced",
            ])
        
        return suggestions
    
    async def generate(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Generate code asynchronously using AI"""
        start_time = datetime.now()
        
        client = await self._get_client()
        system_prompt = self._system_prompts.get(
            request.generation_type, 
            self._system_prompts[GenerationType.GENERIC]
        )
        user_prompt = self._build_prompt(request)
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            
            response_text = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            result = self._parse_response(response_text, request)
            result.generation_time = (datetime.now() - start_time).total_seconds()
            result.tokens_used = tokens_used
            result.confidence_score = 0.9  # Could be based on model confidence
            
            # Store in history
            self._generation_history.append({
                'request': request.description,
                'type': request.generation_type.value,
                'tokens': tokens_used,
                'time': result.generation_time,
            })
            
            logger.info(f"Generated {request.generation_type.value}: {result.filename}")
            return result
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise
    
    def generate_sync(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Generate code synchronously using AI"""
        start_time = datetime.now()
        
        client = self._get_sync_client()
        system_prompt = self._system_prompts.get(
            request.generation_type,
            self._system_prompts[GenerationType.GENERIC]
        )
        user_prompt = self._build_prompt(request)
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            
            response_text = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            result = self._parse_response(response_text, request)
            result.generation_time = (datetime.now() - start_time).total_seconds()
            result.tokens_used = tokens_used
            result.confidence_score = 0.9
            
            logger.info(f"Generated {request.generation_type.value}: {result.filename}")
            return result
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise
    
    async def generate_multiple(
        self, 
        requests: List[CodeGenerationRequest]
    ) -> List[GeneratedCode]:
        """Generate multiple pieces of code concurrently"""
        tasks = [self.generate(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Generation {i} failed: {result}")
            else:
                successful.append(result)
        
        return successful
    
    async def generate_component(
        self,
        component_type: str,
        name: str,
        description: str,
        **kwargs
    ) -> GeneratedCode:
        """Convenience method to generate a specific component"""
        # Map component types to generation types and languages
        type_mapping = {
            'flutter_widget': (GenerationType.FLUTTER_WIDGET, CodeLanguage.DART),
            'flutter_screen': (GenerationType.FLUTTER_SCREEN, CodeLanguage.DART),
            'flutter_service': (GenerationType.FLUTTER_SERVICE, CodeLanguage.DART),
            'api_endpoint': (GenerationType.FASTAPI_ENDPOINT, CodeLanguage.PYTHON),
            'api_model': (GenerationType.FASTAPI_MODEL, CodeLanguage.PYTHON),
            'api_service': (GenerationType.FASTAPI_SERVICE, CodeLanguage.PYTHON),
            'database_model': (GenerationType.DATABASE_SCHEMA, CodeLanguage.PYTHON),
            'docker': (GenerationType.DOCKER_CONFIG, CodeLanguage.DOCKERFILE),
            'kubernetes': (GenerationType.KUBERNETES_MANIFEST, CodeLanguage.YAML),
            'unit_test': (GenerationType.TEST_UNIT, CodeLanguage.PYTHON),
            'docs': (GenerationType.DOCUMENTATION, CodeLanguage.MARKDOWN),
        }
        
        gen_type, language = type_mapping.get(
            component_type, 
            (GenerationType.GENERIC, CodeLanguage.PYTHON)
        )
        
        request = CodeGenerationRequest(
            generation_type=gen_type,
            description=f"{name}: {description}",
            language=language,
            context=kwargs.get('context', {}),
            requirements=kwargs.get('requirements', []),
            constraints=kwargs.get('constraints', []),
        )
        
        return await self.generate(request)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about code generation"""
        if not self._generation_history:
            return {'total_generations': 0}
        
        total_tokens = sum(h['tokens'] for h in self._generation_history)
        total_time = sum(h['time'] for h in self._generation_history)
        
        return {
            'total_generations': len(self._generation_history),
            'total_tokens_used': total_tokens,
            'total_generation_time': total_time,
            'average_tokens_per_generation': total_tokens / len(self._generation_history),
            'average_time_per_generation': total_time / len(self._generation_history),
            'types_generated': list(set(h['type'] for h in self._generation_history)),
        }
