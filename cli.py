#!/usr/bin/env python3
"""
Emy-FullStack CLI
Command-line interface for creating and managing AI-powered applications
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.project_manager import (
    ProjectCreator, ProjectConfig, ProjectType, 
    DatabaseType, AuthType
)
from core.ai_generator import (
    AICodeGenerator, CodeGenerationRequest, GenerationType, CodeLanguage
)


def print_banner():
    """Print CLI banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║           🚀 Emy-FullStack AI Developer System 🚀          ║
║        Autonomous Full-Stack Application Generator         ║
╚═══════════════════════════════════════════════════════════╝
    """)


def create_project_interactive():
    """Interactive project creation wizard"""
    print_banner()
    print("Let's create your new project!\n")
    
    # Project name
    name = input("Project name: ").strip()
    if not name:
        print("Error: Project name is required")
        return
    
    # Description
    description = input("Description (optional): ").strip() or f"A {name} application"
    
    # Project type
    print("\nProject type:")
    print("  1. flutter_mobile  - Flutter mobile app only")
    print("  2. flutter_web     - Flutter web app only") 
    print("  3. flutter_full    - Flutter mobile + web")
    print("  4. fastapi_backend - FastAPI backend only")
    print("  5. fullstack       - Flutter + FastAPI (recommended)")
    
    type_choice = input("\nChoose type [5]: ").strip() or "5"
    type_map = {
        "1": ProjectType.FLUTTER_MOBILE,
        "2": ProjectType.FLUTTER_WEB,
        "3": ProjectType.FLUTTER_FULL,
        "4": ProjectType.FASTAPI_BACKEND,
        "5": ProjectType.FULLSTACK,
    }
    project_type = type_map.get(type_choice, ProjectType.FULLSTACK)
    
    # Database (if backend)
    database = DatabaseType.POSTGRESQL
    if project_type in [ProjectType.FASTAPI_BACKEND, ProjectType.FULLSTACK]:
        print("\nDatabase:")
        print("  1. postgresql (recommended)")
        print("  2. mysql")
        print("  3. sqlite")
        print("  4. mongodb")
        print("  5. none")
        
        db_choice = input("\nChoose database [1]: ").strip() or "1"
        db_map = {
            "1": DatabaseType.POSTGRESQL,
            "2": DatabaseType.MYSQL,
            "3": DatabaseType.SQLITE,
            "4": DatabaseType.MONGODB,
            "5": DatabaseType.NONE,
        }
        database = db_map.get(db_choice, DatabaseType.POSTGRESQL)
    
    # Authentication
    print("\nAuthentication:")
    print("  1. jwt (recommended)")
    print("  2. oauth2")
    print("  3. firebase")
    print("  4. none")
    
    auth_choice = input("\nChoose auth [1]: ").strip() or "1"
    auth_map = {
        "1": AuthType.JWT,
        "2": AuthType.OAUTH2,
        "3": AuthType.FIREBASE,
        "4": AuthType.NONE,
    }
    auth = auth_map.get(auth_choice, AuthType.JWT)
    
    # Features
    print("\nFeatures to include:")
    features = []
    
    if input("User authentication? [Y/n]: ").strip().lower() != "n":
        features.append("user_auth")
    
    if input("API endpoints? [Y/n]: ").strip().lower() != "n":
        features.append("api_endpoints")
    
    if input("Database integration? [Y/n]: ").strip().lower() != "n":
        features.append("database")
    
    if input("Docker support? [Y/n]: ").strip().lower() != "n":
        features.append("docker")
    
    # Output path
    default_path = f"./{name.lower().replace(' ', '-')}"
    output_path = input(f"\nOutput path [{default_path}]: ").strip() or default_path
    
    # Additional options
    include_tests = input("Include tests? [Y/n]: ").strip().lower() != "n"
    include_docs = input("Include documentation? [Y/n]: ").strip().lower() != "n"
    use_openai = input("Enable AI code generation? [Y/n]: ").strip().lower() != "n"
    
    # Create config
    config = ProjectConfig(
        name=name,
        description=description,
        project_type=project_type,
        database=database,
        auth=auth,
        features=features if features else ["user_auth", "api_endpoints", "database", "docker"],
        output_path=output_path,
        include_tests=include_tests,
        include_docker="docker" in features,
        include_docs=include_docs,
        use_openai=use_openai,
    )
    
    # Confirm
    print("\n" + "=" * 50)
    print("Project Configuration:")
    print(f"  Name: {name}")
    print(f"  Type: {project_type.value}")
    print(f"  Database: {database.value}")
    print(f"  Auth: {auth.value}")
    print(f"  Features: {', '.join(features)}")
    print(f"  Path: {output_path}")
    print("=" * 50)
    
    confirm = input("\nCreate project? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("Cancelled.")
        return
    
    # Create project
    print("\n🔨 Creating project...")
    creator = ProjectCreator()
    result = creator.create_project(config)
    
    print(f"\n✅ Project created successfully!")
    print(f"   Path: {result['path']}")
    print(f"   Files: {len(result['files_created'])}")
    
    # Next steps
    print("\n📋 Next steps:")
    
    if project_type == ProjectType.FULLSTACK:
        print(f"""
  1. cd {output_path}
  2. Start services: docker-compose up -d
  3. Backend: http://localhost:8000/docs
  4. Frontend: cd frontend && flutter run
""")
    elif project_type == ProjectType.FASTAPI_BACKEND:
        print(f"""
  1. cd {output_path}
  2. python -m venv venv && source venv/bin/activate
  3. pip install -r requirements.txt
  4. cp .env.example .env
  5. uvicorn main:app --reload
  6. Open: http://localhost:8000/docs
""")
    else:  # Flutter
        print(f"""
  1. cd {output_path}
  2. flutter pub get
  3. flutter run
""")


def create_project_cli(args):
    """Create project from CLI arguments"""
    type_map = {
        "flutter_mobile": ProjectType.FLUTTER_MOBILE,
        "flutter_web": ProjectType.FLUTTER_WEB,
        "flutter_full": ProjectType.FLUTTER_FULL,
        "fastapi": ProjectType.FASTAPI_BACKEND,
        "fullstack": ProjectType.FULLSTACK,
    }
    
    db_map = {
        "postgresql": DatabaseType.POSTGRESQL,
        "mysql": DatabaseType.MYSQL,
        "sqlite": DatabaseType.SQLITE,
        "mongodb": DatabaseType.MONGODB,
        "none": DatabaseType.NONE,
    }
    
    auth_map = {
        "jwt": AuthType.JWT,
        "oauth2": AuthType.OAUTH2,
        "firebase": AuthType.FIREBASE,
        "none": AuthType.NONE,
    }
    
    config = ProjectConfig(
        name=args.name,
        description=args.description or f"A {args.name} application",
        project_type=type_map.get(args.type, ProjectType.FULLSTACK),
        database=db_map.get(args.database, DatabaseType.POSTGRESQL),
        auth=auth_map.get(args.auth, AuthType.JWT),
        output_path=args.output or f"./{args.name.lower().replace(' ', '-')}",
        include_tests=not args.no_tests,
        include_docker=not args.no_docker,
        include_docs=not args.no_docs,
        use_openai=args.openai,
    )
    
    print_banner()
    print(f"🔨 Creating {args.type} project: {args.name}")
    
    creator = ProjectCreator()
    result = creator.create_project(config)
    
    print(f"\n✅ Project created: {result['path']}")
    print(f"   Files: {len(result['files_created'])}")


def generate_code_cli(args):
    """Generate code using AI"""
    print_banner()
    
    if not os.getenv("OPENAI_API_KEY") and not args.api_key:
        print("Error: OPENAI_API_KEY not set. Use --api-key or set environment variable.")
        return
    
    type_map = {
        "flutter_widget": (GenerationType.FLUTTER_WIDGET, CodeLanguage.DART),
        "flutter_screen": (GenerationType.FLUTTER_SCREEN, CodeLanguage.DART),
        "api_endpoint": (GenerationType.FASTAPI_ENDPOINT, CodeLanguage.PYTHON),
        "api_model": (GenerationType.FASTAPI_MODEL, CodeLanguage.PYTHON),
        "database": (GenerationType.DATABASE_SCHEMA, CodeLanguage.PYTHON),
        "docker": (GenerationType.DOCKER_CONFIG, CodeLanguage.DOCKERFILE),
        "test": (GenerationType.TEST_UNIT, CodeLanguage.PYTHON),
    }
    
    gen_type, language = type_map.get(
        args.type, 
        (GenerationType.GENERIC, CodeLanguage.PYTHON)
    )
    
    generator = AICodeGenerator(api_key=args.api_key)
    
    request = CodeGenerationRequest(
        generation_type=gen_type,
        description=args.description,
        language=language,
        requirements=args.requirements.split(",") if args.requirements else [],
    )
    
    print(f"🤖 Generating {args.type}...")
    print(f"   Description: {args.description}")
    
    try:
        result = generator.generate_sync(request)
        
        print(f"\n✅ Generated: {result.filename}")
        print(f"   Dependencies: {', '.join(result.dependencies) or 'none'}")
        print(f"   Time: {result.generation_time:.2f}s")
        
        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.code)
            print(f"   Saved to: {args.output}")
        else:
            print("\n" + "=" * 50)
            print(result.code)
            print("=" * 50)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


def list_agents():
    """List available agents"""
    print_banner()
    print("Available Agents:\n")
    
    from agents import (
        FrontendAgent, BackendAgent, DatabaseAgent,
        DevOpsAgent, QAAgent, UIUXAgent,
        SecurityAgent, AIMLAgent, ProjectManagerAgent,
    )
    
    agents = [
        ("Frontend", FrontendAgent(), "Flutter UI, state management, API integration"),
        ("Backend", BackendAgent(), "FastAPI endpoints, authentication, services"),
        ("Database", DatabaseAgent(), "Schema design, migrations, optimization"),
        ("DevOps", DevOpsAgent(), "Docker, Kubernetes, CI/CD pipelines"),
        ("QA", QAAgent(), "Unit tests, integration tests, coverage"),
        ("UI/UX", UIUXAgent(), "Wireframes, layouts, design systems"),
        ("Security", SecurityAgent(), "Authentication, encryption, vulnerability scans"),
        ("AI/ML", AIMLAgent(), "Model integration, predictions, training"),
        ("Project Manager", ProjectManagerAgent(), "Task allocation, sprint planning, coordination"),
    ]
    
    for name, agent, desc in agents:
        print(f"  🤖 {name}")
        print(f"     Capabilities: {', '.join(agent.capabilities[:4])}...")
        print(f"     {desc}")
        print()


def status():
    """Show system status"""
    print_banner()
    print("System Status:\n")
    
    # Check dependencies
    checks = []
    
    try:
        import openai
        checks.append(("OpenAI", "✅ Installed"))
    except ImportError:
        checks.append(("OpenAI", "❌ Not installed (pip install openai)"))
    
    try:
        import celery
        checks.append(("Celery", "✅ Installed"))
    except ImportError:
        checks.append(("Celery", "⚠️ Optional (pip install celery)"))
    
    try:
        import redis
        checks.append(("Redis", "✅ Installed"))
    except ImportError:
        checks.append(("Redis", "⚠️ Optional (pip install redis)"))
    
    # Check API key
    if os.getenv("OPENAI_API_KEY"):
        checks.append(("OPENAI_API_KEY", "✅ Configured"))
    else:
        checks.append(("OPENAI_API_KEY", "⚠️ Not set (required for AI generation)"))
    
    for name, status in checks:
        print(f"  {name}: {status}")
    
    print("\n  Agents: 9 available")
    print("  Project types: 5 (flutter_mobile, flutter_web, flutter_full, fastapi, fullstack)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Emy-FullStack AI Developer System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive project creation
  emy new
  
  # Quick project creation
  emy create my-app --type fullstack
  
  # Generate code with AI
  emy generate flutter_widget "User profile card with avatar and stats"
  
  # List available agents
  emy agents
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # New (interactive)
    new_parser = subparsers.add_parser("new", help="Create new project (interactive)")
    
    # Create (CLI)
    create_parser = subparsers.add_parser("create", help="Create new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--type", "-t", default="fullstack",
                              choices=["flutter_mobile", "flutter_web", "flutter_full", "fastapi", "fullstack"],
                              help="Project type")
    create_parser.add_argument("--database", "-d", default="postgresql",
                              choices=["postgresql", "mysql", "sqlite", "mongodb", "none"],
                              help="Database type")
    create_parser.add_argument("--auth", "-a", default="jwt",
                              choices=["jwt", "oauth2", "firebase", "none"],
                              help="Authentication type")
    create_parser.add_argument("--output", "-o", help="Output path")
    create_parser.add_argument("--description", help="Project description")
    create_parser.add_argument("--no-tests", action="store_true", help="Skip tests")
    create_parser.add_argument("--no-docker", action="store_true", help="Skip Docker")
    create_parser.add_argument("--no-docs", action="store_true", help="Skip documentation")
    create_parser.add_argument("--openai", action="store_true", help="Enable OpenAI integration")
    
    # Generate
    gen_parser = subparsers.add_parser("generate", help="Generate code with AI")
    gen_parser.add_argument("type", 
                           choices=["flutter_widget", "flutter_screen", "api_endpoint", 
                                   "api_model", "database", "docker", "test"],
                           help="Type of code to generate")
    gen_parser.add_argument("description", help="Description of what to generate")
    gen_parser.add_argument("--output", "-o", help="Output file path")
    gen_parser.add_argument("--requirements", "-r", help="Comma-separated requirements")
    gen_parser.add_argument("--api-key", help="OpenAI API key")
    
    # Agents
    subparsers.add_parser("agents", help="List available agents")
    
    # Status
    subparsers.add_parser("status", help="Show system status")
    
    args = parser.parse_args()
    
    if args.command == "new":
        create_project_interactive()
    elif args.command == "create":
        create_project_cli(args)
    elif args.command == "generate":
        generate_code_cli(args)
    elif args.command == "agents":
        list_agents()
    elif args.command == "status":
        status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
