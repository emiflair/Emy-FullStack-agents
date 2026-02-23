"""
Core module for Emy-FullStack AI Developer System
Contains AI integration, code generation, and project management utilities
"""

from .ai_generator import AICodeGenerator, CodeGenerationRequest, GeneratedCode
from .project_manager import ProjectCreator, ProjectConfig

__all__ = [
    'AICodeGenerator',
    'CodeGenerationRequest', 
    'GeneratedCode',
    'ProjectCreator',
    'ProjectConfig',
]
