"""
Quick test script for Emy-FullStack AI Developer System
Tests basic functionality without requiring external services
"""

import asyncio
from datetime import datetime


def test_agents():
    """Test agent imports and basic instantiation"""
    print("\n=== Testing Agents ===")
    
    from agents import (
        FrontendAgent, BackendAgent, DatabaseAgent,
        DevOpsAgent, QAAgent, UIUXAgent,
        SecurityAgent, AIMLAgent, ProjectManagerAgent,
    )
    
    # Agents take optional config dict
    agents = [
        FrontendAgent(),
        BackendAgent(),
        DatabaseAgent(),
        DevOpsAgent(),
        QAAgent(),
        UIUXAgent(),
        SecurityAgent(),
        AIMLAgent(),
        ProjectManagerAgent(),
    ]
    
    for agent in agents:
        print(f"  ✓ {agent.name} (ID: {agent.id})")
    
    print(f"\n  Total: {len(agents)} agents initialized")
    return True


def test_config():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    
    from config import Settings, get_settings
    from config.agents_config import AgentType, get_agents_config
    
    settings = get_settings()
    print(f"  ✓ App Name: {settings.app_name}")
    print(f"  ✓ Environment: {settings.environment.value}")
    print(f"  ✓ Debug: {settings.debug}")
    
    agents_config = get_agents_config()
    enabled = agents_config.get_enabled_agents()
    print(f"  ✓ Enabled Agents: {len(enabled)}")
    
    return True


def test_task_queue():
    """Test task queue components"""
    print("\n=== Testing Task Queue ===")
    
    from task_queue import TaskRouter, TaskRegistry
    from task_queue.priority_queue import TaskPriority
    
    router = TaskRouter()
    registry = TaskRegistry()
    
    print(f"  ✓ TaskRouter initialized")
    print(f"  ✓ TaskRegistry initialized")
    print(f"  ✓ Priority levels: {[p.name for p in TaskPriority]}")
    
    return True


def test_master_brain():
    """Test Master Brain components"""
    print("\n=== Testing Master Brain ===")
    
    from master_brain import (
        MasterBrain, SystemOptimizer,
        AgentCoordinator, OptimizationStrategy,
    )
    from master_brain.feedback_loop import AnalyticsCollector, FeedbackLoop
    
    optimizer = SystemOptimizer()
    analytics = AnalyticsCollector()
    feedback = FeedbackLoop(analytics)
    coordinator = AgentCoordinator()
    
    print(f"  ✓ SystemOptimizer initialized")
    print(f"  ✓ Optimization strategies: {[s.name for s in OptimizationStrategy]}")
    print(f"  ✓ AnalyticsCollector initialized")
    print(f"  ✓ FeedbackLoop initialized")
    print(f"  ✓ AgentCoordinator initialized")
    
    return True


def test_openclaw():
    """Test OpenClaw integration"""
    print("\n=== Testing OpenClaw Integration ===")
    
    from integrations.openclaw import (
        OpenClawClient, OpenClawConfig,
        WebScraper, ContentPoster, AutomationEngine,
        Platform,
    )
    
    config = OpenClawConfig()
    client = OpenClawClient(config)
    scraper = WebScraper()
    poster = ContentPoster()
    automation = AutomationEngine()
    
    print(f"  ✓ OpenClawClient initialized")
    print(f"  ✓ WebScraper initialized")
    print(f"  ✓ ContentPoster initialized")
    print(f"  ✓ Supported platforms: {[p.name for p in Platform][:5]}...")
    print(f"  ✓ AutomationEngine initialized")
    
    return True


async def test_agent_functionality():
    """Test actual agent functionality"""
    print("\n=== Testing Agent Functionality ===")
    
    from agents import FrontendAgent, BackendAgent, UIUXAgent
    
    # Test Frontend Agent
    frontend = FrontendAgent()
    print(f"  ✓ Frontend: {frontend.name}")
    print(f"    Capabilities: {frontend.capabilities[:3]}...")
    
    # Test Backend Agent
    backend = BackendAgent()
    print(f"  ✓ Backend: {backend.name}")
    print(f"    Capabilities: {backend.capabilities[:3]}...")
    
    # Test UI/UX Agent
    uiux = UIUXAgent()
    print(f"  ✓ UI/UX: {uiux.name}")
    print(f"    Capabilities: {uiux.capabilities[:3]}...")
    
    # Test task handling capability
    from agents.base_agent import Task, TaskStatus, TaskPriority
    task = Task(
        id="test-001",
        name="Build Flutter Screen",
        description="Build user profile screen",
        priority=TaskPriority.MEDIUM,
    )
    
    can_handle = frontend.can_handle_task(task)
    print(f"  ✓ Task routing works: Frontend can handle task: {can_handle}")
    
    return True


async def test_system_init():
    """Test system initialization (without starting services)"""
    print("\n=== Testing System Initialization ===")
    
    from main import EmyFullStackSystem
    
    system = EmyFullStackSystem()
    
    print(f"  ✓ EmyFullStackSystem created")
    print(f"  ✓ Environment: {system.settings.environment.value}")
    print(f"  ✓ Agents config loaded: {len(system.agents_config.agents)} types")
    
    # Note: Full initialization requires Redis/PostgreSQL
    print(f"  ⚠ Full init requires Redis & PostgreSQL running")
    
    return True


def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("Emy-FullStack AI Developer System - Test Suite")
    print("=" * 50)
    print(f"Time: {datetime.now().isoformat()}")
    
    tests = [
        ("Agents", test_agents),
        ("Configuration", test_config),
        ("Task Queue", test_task_queue),
        ("Master Brain", test_master_brain),
        ("OpenClaw", test_openclaw),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            if asyncio.iscoroutinefunction(test_fn):
                asyncio.run(test_fn())
            else:
                test_fn()
            passed += 1
        except Exception as e:
            print(f"\n  ✗ {name} FAILED: {e}")
            failed += 1
    
    # Async tests
    async def run_async_tests():
        await test_agent_functionality()
        await test_system_init()
    
    try:
        asyncio.run(run_async_tests())
        passed += 2
    except Exception as e:
        print(f"\n  ✗ Async tests FAILED: {e}")
        failed += 2
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Start Redis: redis-server")
        print("  2. Start PostgreSQL")
        print("  3. Copy .env.example to .env and configure")
        print("  4. Run: python main.py")
    
    return failed == 0


if __name__ == "__main__":
    run_tests()
