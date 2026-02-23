"""
Frontend Developer Agent for Emy-FullStack AI Developer System
Handles Flutter UI development, API connections, and UI state management.
"""

import asyncio
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent, Task


class FrontendAgent(BaseAgent):
    """
    Frontend Developer Agent responsible for:
    - Building Flutter UI screens for mobile/web
    - Connecting UI to backend APIs  
    - Displaying task progress
    - Input validation
    - State management
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="Frontend",
            description="Builds Flutter UI screens and connects them to backend APIs",
            capabilities=[
                "flutter_ui",
                "api_connection",
                "state_management",
                "input_validation",
                "responsive_design",
                "widget_generation",
                "navigation",
                "theming"
            ],
            config=config or {}
        )
        
        # Flutter-specific state
        self.generated_widgets: List[Dict] = []
        self.screens: List[Dict] = []
        self.api_connections: List[Dict] = []

    async def execute_task(self, task: Task) -> Any:
        """Execute frontend development task."""
        task_type = task.metadata.get("type", "general")
        
        handlers = {
            "flutter_ui": self._build_flutter_ui,
            "api_connection": self._connect_api,
            "widget_generation": self._generate_widget,
            "screen_creation": self._create_screen,
            "input_validation": self._implement_validation,
            "state_management": self._setup_state_management,
        }
        
        handler = handlers.get(task_type, self._handle_general_task)
        return await handler(task)

    async def _build_flutter_ui(self, task: Task) -> Dict[str, Any]:
        """Build Flutter UI based on task specifications."""
        self.log(f"Building Flutter UI for: {task.name}")
        
        screen_name = task.metadata.get("screen_name", "DefaultScreen")
        components = task.metadata.get("components", [])
        
        # Generate Flutter code structure
        flutter_code = self._generate_flutter_screen_template(screen_name, components)
        
        screen_info = {
            "name": screen_name,
            "code": flutter_code,
            "components": components,
            "api_endpoints": task.metadata.get("api_endpoints", [])
        }
        self.screens.append(screen_info)
        
        return {
            "status": "success",
            "screen": screen_info,
            "message": f"Generated Flutter screen: {screen_name}"
        }

    async def _connect_api(self, task: Task) -> Dict[str, Any]:
        """Connect UI to backend APIs."""
        self.log(f"Connecting to API: {task.metadata.get('endpoint', 'unknown')}")
        
        endpoint = task.metadata.get("endpoint", "")
        method = task.metadata.get("method", "GET")
        
        api_connection = {
            "endpoint": endpoint,
            "method": method,
            "headers": task.metadata.get("headers", {}),
            "model": task.metadata.get("model", "dynamic")
        }
        
        # Generate API service code
        service_code = self._generate_api_service(api_connection)
        api_connection["code"] = service_code
        
        self.api_connections.append(api_connection)
        
        return {
            "status": "success",
            "connection": api_connection,
            "message": f"Connected to API: {endpoint}"
        }

    async def _generate_widget(self, task: Task) -> Dict[str, Any]:
        """Generate Flutter widget."""
        widget_name = task.metadata.get("widget_name", "CustomWidget")
        widget_type = task.metadata.get("widget_type", "stateless")
        
        self.log(f"Generating {widget_type} widget: {widget_name}")
        
        widget_code = self._create_widget_template(widget_name, widget_type, task.metadata)
        
        widget_info = {
            "name": widget_name,
            "type": widget_type,
            "code": widget_code
        }
        self.generated_widgets.append(widget_info)
        
        return {
            "status": "success",
            "widget": widget_info,
            "message": f"Generated widget: {widget_name}"
        }

    async def _create_screen(self, task: Task) -> Dict[str, Any]:
        """Create a new screen."""
        return await self._build_flutter_ui(task)

    async def _implement_validation(self, task: Task) -> Dict[str, Any]:
        """Implement input validation."""
        self.log(f"Implementing validation for: {task.name}")
        
        fields = task.metadata.get("fields", [])
        validation_rules = []
        
        for field in fields:
            rule = {
                "field": field.get("name", ""),
                "type": field.get("type", "text"),
                "required": field.get("required", True),
                "validators": self._get_validators(field)
            }
            validation_rules.append(rule)
        
        return {
            "status": "success",
            "validation_rules": validation_rules,
            "message": f"Implemented validation for {len(fields)} fields"
        }

    async def _setup_state_management(self, task: Task) -> Dict[str, Any]:
        """Setup state management (Riverpod/Provider/BLoC)."""
        state_manager = task.metadata.get("state_manager", "riverpod")
        self.log(f"Setting up {state_manager} state management")
        
        state_code = self._generate_state_management_code(state_manager, task.metadata)
        
        return {
            "status": "success",
            "state_manager": state_manager,
            "code": state_code,
            "message": f"Setup {state_manager} state management"
        }

    async def _handle_general_task(self, task: Task) -> Dict[str, Any]:
        """Handle general frontend tasks."""
        self.log(f"Handling general task: {task.name}")
        
        return {
            "status": "success",
            "message": f"Processed frontend task: {task.name}",
            "details": task.metadata
        }

    def _generate_flutter_screen_template(self, screen_name: str, components: List) -> str:
        """Generate Flutter screen template code."""
        return f'''
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class {screen_name} extends ConsumerStatefulWidget {{
  const {screen_name}({{super.key}});

  @override
  ConsumerState<{screen_name}> createState() => _{screen_name}State();
}}

class _{screen_name}State extends ConsumerState<{screen_name}> {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{screen_name}'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // TODO: Add generated components
              {self._generate_component_placeholders(components)}
            ],
          ),
        ),
      ),
    );
  }}
}}
'''

    def _generate_component_placeholders(self, components: List) -> str:
        """Generate component placeholders."""
        if not components:
            return "const Text('Content goes here'),"
        return "\n              ".join([f"// {comp}Widget()," for comp in components])

    def _generate_api_service(self, connection: Dict) -> str:
        """Generate API service code."""
        return f'''
import 'package:dio/dio.dart';

class ApiService {{
  final Dio _dio = Dio();
  
  Future<dynamic> {connection['method'].lower()}Request() async {{
    try {{
      final response = await _dio.{connection['method'].lower()}('{connection['endpoint']}');
      return response.data;
    }} catch (e) {{
      throw Exception('API Error: $e');
    }}
  }}
}}
'''

    def _create_widget_template(self, name: str, widget_type: str, metadata: Dict) -> str:
        """Create widget template."""
        if widget_type == "stateful":
            return f'''
import 'package:flutter/material.dart';

class {name} extends StatefulWidget {{
  const {name}({{super.key}});

  @override
  State<{name}> createState() => _{name}State();
}}

class _{name}State extends State<{name}> {{
  @override
  Widget build(BuildContext context) {{
    return Container(
      child: const Text('{name}'),
    );
  }}
}}
'''
        else:
            return f'''
import 'package:flutter/material.dart';

class {name} extends StatelessWidget {{
  const {name}({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Container(
      child: const Text('{name}'),
    );
  }}
}}
'''

    def _get_validators(self, field: Dict) -> List[str]:
        """Get validators for a field type."""
        validators = []
        field_type = field.get("type", "text")
        
        if field.get("required"):
            validators.append("required")
        
        type_validators = {
            "email": ["email_format"],
            "phone": ["phone_format"],
            "number": ["numeric"],
            "url": ["url_format"],
            "password": ["min_length_8", "has_special_char"]
        }
        
        validators.extend(type_validators.get(field_type, []))
        return validators

    def _generate_state_management_code(self, manager: str, metadata: Dict) -> str:
        """Generate state management code."""
        if manager == "riverpod":
            return '''
import 'package:flutter_riverpod/flutter_riverpod.dart';

final appStateProvider = StateNotifierProvider<AppStateNotifier, AppState>((ref) {
  return AppStateNotifier();
});

class AppState {
  final bool isLoading;
  final String? error;
  
  AppState({this.isLoading = false, this.error});
}

class AppStateNotifier extends StateNotifier<AppState> {
  AppStateNotifier() : super(AppState());
  
  void setLoading(bool loading) {
    state = AppState(isLoading: loading);
  }
}
'''
        return "// State management code placeholder"
