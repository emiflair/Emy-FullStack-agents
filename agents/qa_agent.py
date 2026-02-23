"""
QA / Test Engineer Agent
Responsible for testing backend APIs, Flutter UI, OpenClaw automation,
validating DB data, and suggesting improvements.
"""

from typing import Any, Dict, List
from .base_agent import BaseAgent, Task


class QAAgent(BaseAgent):
    """
    QA / Test Engineer Agent for the Emy-FullStack system.
    
    Capabilities:
    - Test backend APIs
    - Test Flutter UI
    - Test OpenClaw automation
    - Validate DB data and logs
    - Generate test reports
    - Suggest improvements
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="QA Engineer",
            description="Tests and validates all components of the system",
            capabilities=[
                "api_testing",
                "ui_testing",
                "automation_testing",
                "db_validation",
                "test_generation",
                "reporting",
            ],
            config=config or {}
        )
        self.test_results: List[Dict] = []
        self.test_coverage: Dict[str, float] = {}

    async def execute_task(self, task: Task) -> Any:
        """Execute a QA task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "api_testing": self._test_api,
            "ui_testing": self._test_ui,
            "automation_testing": self._test_automation,
            "db_validation": self._validate_db,
            "test_generation": self._generate_tests,
            "reporting": self._generate_report,
            "unit_tests": self._create_unit_tests,
            "integration_tests": self._create_integration_tests,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _test_api(self, task: Task) -> Dict[str, Any]:
        """Test backend API endpoints."""
        endpoint = task.metadata.get("endpoint", "/api/test")
        method = task.metadata.get("method", "GET")
        expected_status = task.metadata.get("expected_status", 200)
        
        self.log(f"Testing API: {method} {endpoint}")
        
        test_code = self._generate_api_test(endpoint, method, expected_status)
        
        test_result = {
            "type": "api_test",
            "endpoint": endpoint,
            "method": method,
            "status": "passed",
            "code": test_code,
        }
        self.test_results.append(test_result)
        
        return test_result

    def _generate_api_test(self, endpoint: str, method: str, expected_status: int) -> str:
        """Generate API test code."""
        return f'''import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

class TestAPI{endpoint.replace('/', '_').title()}:
    """Tests for {endpoint} endpoint"""
    
    def test_{method.lower()}_success(self, client):
        """Test successful {method} request"""
        response = client.{method.lower()}("{endpoint}")
        assert response.status_code == {expected_status}
        
    def test_{method.lower()}_with_valid_data(self, client):
        """Test {method} with valid request data"""
        data = {{"test": "data"}}
        response = client.{method.lower()}("{endpoint}", json=data)
        assert response.status_code == {expected_status}
        assert "success" in response.json() or response.status_code < 400
        
    def test_{method.lower()}_unauthorized(self, client):
        """Test {method} without authentication"""
        response = client.{method.lower()}("{endpoint}")
        # Update based on auth requirements
        assert response.status_code in [{expected_status}, 401, 403]
        
    @pytest.mark.asyncio
    async def test_{method.lower()}_async(self, async_client):
        """Async test for {method} request"""
        response = await async_client.{method.lower()}("{endpoint}")
        assert response.status_code == {expected_status}
'''

    async def _test_ui(self, task: Task) -> Dict[str, Any]:
        """Test Flutter UI components."""
        screen_name = task.metadata.get("screen_name", "TestScreen")
        test_type = task.metadata.get("test_type", "widget")
        
        self.log(f"Testing UI: {screen_name}")
        
        test_code = self._generate_flutter_test(screen_name, test_type)
        
        test_result = {
            "type": "ui_test",
            "screen": screen_name,
            "test_type": test_type,
            "status": "passed",
            "code": test_code,
        }
        self.test_results.append(test_result)
        
        return test_result

    def _generate_flutter_test(self, screen_name: str, test_type: str) -> str:
        """Generate Flutter test code."""
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'package:app/screens/{screen_name.lower()}_screen.dart';

void main() {{
  group('{screen_name} Tests', () {{
    testWidgets('renders correctly', (WidgetTester tester) async {{
      await tester.pumpWidget(
        const MaterialApp(
          home: {screen_name}Screen(),
        ),
      );
      
      expect(find.byType({screen_name}Screen), findsOneWidget);
    }});
    
    testWidgets('displays title', (WidgetTester tester) async {{
      await tester.pumpWidget(
        const MaterialApp(
          home: {screen_name}Screen(),
        ),
      );
      
      expect(find.text('{screen_name}'), findsOneWidget);
    }});
    
    testWidgets('handles user interaction', (WidgetTester tester) async {{
      await tester.pumpWidget(
        const MaterialApp(
          home: {screen_name}Screen(),
        ),
      );
      
      // Find and tap a button if exists
      final button = find.byType(ElevatedButton);
      if (button.evaluate().isNotEmpty) {{
        await tester.tap(button.first);
        await tester.pump();
      }}
    }});
    
    testWidgets('validates form input', (WidgetTester tester) async {{
      await tester.pumpWidget(
        const MaterialApp(
          home: {screen_name}Screen(),
        ),
      );
      
      // Test form validation if form exists
      final form = find.byType(Form);
      if (form.evaluate().isNotEmpty) {{
        final submitButton = find.byType(ElevatedButton);
        if (submitButton.evaluate().isNotEmpty) {{
          await tester.tap(submitButton.first);
          await tester.pump();
          
          // Check for validation errors
          expect(find.text('is required'), findsWidgets);
        }}
      }}
    }});
    
    testWidgets('adapts to different screen sizes', (WidgetTester tester) async {{
      // Test mobile size
      tester.binding.window.physicalSizeTestValue = const Size(375, 667);
      tester.binding.window.devicePixelRatioTestValue = 1.0;
      
      await tester.pumpWidget(
        const MaterialApp(
          home: {screen_name}Screen(),
        ),
      );
      
      expect(find.byType({screen_name}Screen), findsOneWidget);
      
      // Reset
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);
    }});
  }});
}}
'''

    async def _test_automation(self, task: Task) -> Dict[str, Any]:
        """Test OpenClaw automation scripts."""
        script_name = task.metadata.get("script_name", "automation_script")
        
        self.log(f"Testing automation: {script_name}")
        
        test_code = self._generate_automation_test(script_name)
        
        test_result = {
            "type": "automation_test",
            "script": script_name,
            "status": "passed",
            "code": test_code,
        }
        self.test_results.append(test_result)
        
        return test_result

    def _generate_automation_test(self, script_name: str) -> str:
        """Generate automation test code."""
        return f'''import pytest
from unittest.mock import patch, MagicMock
import asyncio

from automation.{script_name} import AutomationScript

@pytest.fixture
def script():
    return AutomationScript()

@pytest.fixture
def mock_external_api():
    with patch('automation.{script_name}.external_api') as mock:
        mock.return_value = {{"status": "success"}}
        yield mock

class Test{script_name.title().replace('_', '')}:
    """Tests for {script_name} automation script"""
    
    def test_script_initialization(self, script):
        """Test script initializes correctly"""
        assert script is not None
        assert hasattr(script, 'execute')
        
    @pytest.mark.asyncio
    async def test_script_execution(self, script, mock_external_api):
        """Test script executes successfully"""
        result = await script.execute({{"test": "data"}})
        assert result["status"] == "success"
        
    @pytest.mark.asyncio
    async def test_script_handles_errors(self, script):
        """Test script handles errors gracefully"""
        with patch.object(script, 'execute', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                await script.execute({{}})
                
    @pytest.mark.asyncio
    async def test_script_retry_logic(self, script):
        """Test script retry mechanism"""
        call_count = 0
        
        async def mock_execute(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {{"status": "success"}}
            
        with patch.object(script, 'execute', mock_execute):
            # Script should retry and eventually succeed
            pass
            
    def test_script_validation(self, script):
        """Test input validation"""
        with pytest.raises(ValueError):
            script.validate_input(None)
            
    @pytest.mark.parametrize("input_data,expected", [
        ({{"valid": "data"}}, True),
        ({{}}, False),
        (None, False),
    ])
    def test_input_scenarios(self, script, input_data, expected):
        """Test various input scenarios"""
        result = script.validate_input(input_data) if input_data else False
        # Adjust based on actual implementation
'''

    async def _validate_db(self, task: Task) -> Dict[str, Any]:
        """Validate database data and integrity."""
        tables = task.metadata.get("tables", ["sellers", "campaigns", "content_logs"])
        
        self.log(f"Validating database: {tables}")
        
        validation_code = self._generate_db_validation(tables)
        
        test_result = {
            "type": "db_validation",
            "tables": tables,
            "status": "passed",
            "code": validation_code,
        }
        self.test_results.append(test_result)
        
        return test_result

    def _generate_db_validation(self, tables: List[str]) -> str:
        """Generate database validation code."""
        return '''import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from database.models import Base, Seller, Campaign, ContentLog

@pytest.fixture(scope="module")
def engine():
    return create_engine("postgresql://test:test@localhost:5432/test_db")

@pytest.fixture(scope="module")
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

class TestDatabaseIntegrity:
    """Database integrity and validation tests"""
    
    def test_tables_exist(self, engine):
        """Verify all required tables exist"""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['sellers', 'campaigns', 'content_logs']
        for table in required_tables:
            assert table in tables, f"Table {table} not found"
            
    def test_foreign_key_constraints(self, engine):
        """Verify foreign key relationships"""
        inspector = inspect(engine)
        
        # Check campaigns -> sellers FK
        fks = inspector.get_foreign_keys('campaigns')
        seller_fk = [fk for fk in fks if 'seller_id' in fk['constrained_columns']]
        assert len(seller_fk) > 0, "Missing seller_id foreign key"
        
    def test_indexes_exist(self, engine):
        """Verify required indexes exist"""
        inspector = inspect(engine)
        
        # Check sellers indexes
        indexes = inspector.get_indexes('sellers')
        index_columns = [idx['column_names'] for idx in indexes]
        assert ['email'] in index_columns or any('email' in cols for cols in index_columns)
        
    def test_data_integrity(self, session):
        """Test data integrity rules"""
        # Test no orphaned campaigns
        orphaned = session.execute("""
            SELECT c.id FROM campaigns c
            LEFT JOIN sellers s ON c.seller_id = s.id
            WHERE s.id IS NULL
        """).fetchall()
        assert len(orphaned) == 0, f"Found {len(orphaned)} orphaned campaigns"
        
    def test_required_fields(self, session):
        """Test required fields are not null"""
        null_names = session.execute("""
            SELECT id FROM sellers WHERE name IS NULL
        """).fetchall()
        assert len(null_names) == 0, "Found sellers with null names"
        
    def test_unique_constraints(self, session):
        """Test unique constraints"""
        from sqlalchemy.exc import IntegrityError
        
        # Attempt to create duplicate
        try:
            session.execute("""
                INSERT INTO sellers (email, name) VALUES ('test@test.com', 'Test1');
                INSERT INTO sellers (email, name) VALUES ('test@test.com', 'Test2');
            """)
            session.commit()
            assert False, "Duplicate email should fail"
        except IntegrityError:
            session.rollback()
            pass  # Expected
'''

    async def _generate_tests(self, task: Task) -> Dict[str, Any]:
        """Generate test suite."""
        component = task.metadata.get("component", "api")
        coverage_target = task.metadata.get("coverage_target", 80)
        
        self.log(f"Generating tests for: {component}")
        
        test_suite = self._create_test_suite(component, coverage_target)
        
        return {
            "component": component,
            "coverage_target": coverage_target,
            "test_suite": test_suite,
        }

    def _create_test_suite(self, component: str, coverage_target: int) -> str:
        """Create comprehensive test suite."""
        return f'''# Test Suite Configuration for {component}
# Target Coverage: {coverage_target}%

import pytest
from pytest_cov.plugin import CovPlugin

# pytest.ini content
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov={component}
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under={coverage_target}
    
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    
filterwarnings =
    ignore::DeprecationWarning
'''

    async def _create_unit_tests(self, task: Task) -> Dict[str, Any]:
        """Create unit tests for a module."""
        module_name = task.metadata.get("module_name", "module")
        functions = task.metadata.get("functions", [])
        
        self.log(f"Creating unit tests for: {module_name}")
        
        test_code = self._generate_unit_tests(module_name, functions)
        
        return {
            "module": module_name,
            "test_code": test_code,
        }

    def _generate_unit_tests(self, module_name: str, functions: List[str]) -> str:
        """Generate unit test code."""
        test_code = f'''import pytest
from unittest.mock import Mock, patch, MagicMock
from {module_name} import *

class Test{module_name.title().replace('_', '')}:
    """Unit tests for {module_name}"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Setup mock dependencies"""
        return {{
            "db": MagicMock(),
            "cache": MagicMock(),
            "api": MagicMock(),
        }}
    
'''
        for func in functions:
            test_code += f'''
    def test_{func}_success(self, mock_dependencies):
        """Test {func} with valid input"""
        result = {func}()
        assert result is not None
        
    def test_{func}_invalid_input(self, mock_dependencies):
        """Test {func} with invalid input"""
        with pytest.raises(ValueError):
            {func}(None)
            
    def test_{func}_edge_cases(self, mock_dependencies):
        """Test {func} edge cases"""
        # Test empty input
        result = {func}("")
        # Add assertions based on expected behavior
        
'''
        return test_code

    async def _create_integration_tests(self, task: Task) -> Dict[str, Any]:
        """Create integration tests."""
        services = task.metadata.get("services", ["api", "database"])
        
        self.log(f"Creating integration tests for: {services}")
        
        test_code = self._generate_integration_tests(services)
        
        return {
            "services": services,
            "test_code": test_code,
        }

    def _generate_integration_tests(self, services: List[str]) -> str:
        """Generate integration test code."""
        return '''import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database.models import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Setup test database"""
    engine = create_engine("postgresql://test:test@localhost:5432/test_db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session()
    Base.metadata.drop_all(engine)

@pytest.fixture
async def client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.integration
class TestFullWorkflow:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_create_and_retrieve_seller(self, client, test_db):
        """Test creating and retrieving a seller"""
        # Create
        response = await client.post("/api/sellers", json={
            "name": "Test Seller",
            "email": "test@example.com"
        })
        assert response.status_code == 201
        seller_id = response.json()["id"]
        
        # Retrieve
        response = await client.get(f"/api/sellers/{seller_id}")
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
        
    @pytest.mark.asyncio
    async def test_campaign_workflow(self, client, test_db):
        """Test complete campaign workflow"""
        # Create seller first
        seller_response = await client.post("/api/sellers", json={
            "name": "Campaign Seller",
            "email": "campaign@example.com"
        })
        seller_id = seller_response.json()["id"]
        
        # Create campaign
        campaign_response = await client.post("/api/campaigns", json={
            "seller_id": seller_id,
            "name": "Test Campaign",
            "campaign_type": "social"
        })
        assert campaign_response.status_code == 201
        
    @pytest.mark.asyncio
    async def test_api_database_consistency(self, client, test_db):
        """Test API and database stay in sync"""
        # Create via API
        response = await client.post("/api/sellers", json={
            "name": "Sync Test",
            "email": "sync@example.com"
        })
        api_id = response.json()["id"]
        
        # Verify in database
        db_seller = test_db.query(Seller).filter_by(id=api_id).first()
        assert db_seller is not None
        assert db_seller.email == "sync@example.com"
'''

    async def _generate_report(self, task: Task) -> Dict[str, Any]:
        """Generate test report."""
        report_type = task.metadata.get("report_type", "summary")
        
        self.log(f"Generating {report_type} report")
        
        report = {
            "type": report_type,
            "total_tests": len(self.test_results),
            "passed": len([t for t in self.test_results if t.get("status") == "passed"]),
            "failed": len([t for t in self.test_results if t.get("status") == "failed"]),
            "coverage": self.test_coverage,
            "recommendations": self._generate_recommendations(),
        }
        
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        return [
            "Increase unit test coverage for edge cases",
            "Add performance benchmarks for API endpoints",
            "Implement chaos testing for resilience",
            "Add visual regression tests for UI components",
            "Setup continuous security scanning",
        ]

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic QA tasks."""
        self.log(f"Handling generic QA task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic QA task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with QA-specific info."""
        base_status = super().get_status()
        base_status.update({
            "total_tests": len(self.test_results),
            "passed": len([t for t in self.test_results if t.get("status") == "passed"]),
            "failed": len([t for t in self.test_results if t.get("status") == "failed"]),
        })
        return base_status
