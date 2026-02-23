"""
UI/UX Designer Agent
Responsible for defining flows, interactions, visual feedback,
generating Flutter layouts and reusable widgets.
"""

from typing import Any, Dict, List
from .base_agent import BaseAgent, Task


class UIUXAgent(BaseAgent):
    """
    UI/UX Designer Agent for the Emy-FullStack system.
    
    Capabilities:
    - Define flows, interactions, visual feedback
    - Generate Flutter layouts and reusable widgets
    - Ensure mobile-friendly UX
    - Create design system components
    - Generate wireframes and prototypes
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="UI/UX Designer",
            description="Designs user interfaces and experiences",
            capabilities=[
                "wireframe",
                "layout",
                "design_system",
                "interaction",
                "responsive",
                "accessibility",
            ],
            config=config or {}
        )
        self.design_system: Dict[str, Any] = {}
        self.wireframes: List[Dict] = []
        self.components: List[Dict] = []

    async def execute_task(self, task: Task) -> Any:
        """Execute a UI/UX design task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "wireframe": self._create_wireframe,
            "layout": self._design_layout,
            "design_system": self._create_design_system,
            "interaction": self._design_interaction,
            "responsive": self._implement_responsive,
            "accessibility": self._ensure_accessibility,
            "component": self._create_component,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _create_wireframe(self, task: Task) -> Dict[str, Any]:
        """Create wireframe for a screen."""
        screen_name = task.metadata.get("screen_name", "Screen")
        flow = task.metadata.get("flow", [])
        
        self.log(f"Creating wireframe: {screen_name}")
        
        wireframe = {
            "screen": screen_name,
            "flow": flow,
            "elements": self._generate_wireframe_elements(task.metadata),
            "mermaid_diagram": self._generate_flow_diagram(screen_name, flow),
        }
        self.wireframes.append(wireframe)
        
        return wireframe

    def _generate_wireframe_elements(self, metadata: Dict) -> List[Dict]:
        """Generate wireframe elements."""
        elements = metadata.get("elements", [])
        
        default_elements = [
            {"type": "header", "content": "App Bar with navigation"},
            {"type": "body", "content": "Main content area"},
            {"type": "form", "fields": ["input1", "input2"]},
            {"type": "button", "label": "Primary Action"},
            {"type": "footer", "content": "Bottom navigation"},
        ]
        
        return elements if elements else default_elements

    def _generate_flow_diagram(self, screen_name: str, flow: List[str]) -> str:
        """Generate Mermaid flow diagram."""
        if not flow:
            flow = ["Start", "Input", "Processing", "Result", "End"]
        
        diagram = f'''```mermaid
flowchart TD
    A[{flow[0] if flow else 'Start'}] --> B[{screen_name}]
'''
        for i, step in enumerate(flow[1:], start=2):
            prev = chr(65 + i - 1)
            curr = chr(65 + i)
            diagram += f"    {prev}[{flow[i-2]}] --> {curr}[{step}]\n"
        
        diagram += "```"
        return diagram

    async def _design_layout(self, task: Task) -> Dict[str, Any]:
        """Design screen layout."""
        screen_name = task.metadata.get("screen_name", "Screen")
        layout_type = task.metadata.get("layout_type", "single_column")
        
        self.log(f"Designing layout: {screen_name} ({layout_type})")
        
        layout_code = self._generate_layout_code(screen_name, layout_type, task.metadata)
        
        return {
            "screen": screen_name,
            "layout_type": layout_type,
            "code": layout_code,
        }

    def _generate_layout_code(self, screen_name: str, layout_type: str, metadata: Dict) -> str:
        """Generate Flutter layout code."""
        layouts = {
            "single_column": self._single_column_layout,
            "two_column": self._two_column_layout,
            "grid": self._grid_layout,
            "tabs": self._tabs_layout,
            "drawer": self._drawer_layout,
        }
        
        generator = layouts.get(layout_type, self._single_column_layout)
        return generator(screen_name, metadata)

    def _single_column_layout(self, screen_name: str, metadata: Dict) -> str:
        """Generate single column layout."""
        return f'''import 'package:flutter/material.dart';

class {screen_name}Layout extends StatelessWidget {{
  const {screen_name}Layout({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{screen_name}'),
        centerTitle: true,
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header Section
              _buildHeader(),
              const SizedBox(height: 24),
              
              // Content Section
              _buildContent(),
              const SizedBox(height: 24),
              
              // Action Section
              _buildActions(),
            ],
          ),
        ),
      ),
    );
  }}

  Widget _buildHeader() {{
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        Text(
          'Welcome',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 8),
        Text(
          'Description text goes here',
          style: TextStyle(
            fontSize: 16,
            color: Colors.grey,
          ),
        ),
      ],
    );
  }}

  Widget _buildContent() {{
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: const Text('Content goes here'),
    );
  }}

  Widget _buildActions() {{
    return ElevatedButton(
      onPressed: () {{}},
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: const Text('Primary Action'),
    );
  }}
}}
'''

    def _two_column_layout(self, screen_name: str, metadata: Dict) -> str:
        """Generate two column layout for tablets/desktop."""
        return f'''import 'package:flutter/material.dart';

class {screen_name}Layout extends StatelessWidget {{
  const {screen_name}Layout({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      body: Row(
        children: [
          // Left Panel (Navigation/List)
          Expanded(
            flex: 1,
            child: Container(
              color: Theme.of(context).colorScheme.surface,
              child: _buildLeftPanel(),
            ),
          ),
          
          // Divider
          const VerticalDivider(width: 1),
          
          // Right Panel (Detail/Content)
          Expanded(
            flex: 2,
            child: _buildRightPanel(),
          ),
        ],
      ),
    );
  }}

  Widget _buildLeftPanel() {{
    return ListView.builder(
      itemCount: 10,
      itemBuilder: (context, index) {{
        return ListTile(
          leading: CircleAvatar(child: Text('${{index + 1}}')),
          title: Text('Item ${{index + 1}}'),
          subtitle: const Text('Description'),
          onTap: () {{}},
        );
      }},
    );
  }}

  Widget _buildRightPanel() {{
    return const Center(
      child: Text('Select an item to view details'),
    );
  }}
}}
'''

    def _grid_layout(self, screen_name: str, metadata: Dict) -> str:
        """Generate grid layout."""
        columns = metadata.get("columns", 2)
        return f'''import 'package:flutter/material.dart';

class {screen_name}Layout extends StatelessWidget {{
  const {screen_name}Layout({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{screen_name}')),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: {columns},
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: 1,
        ),
        itemCount: 12,
        itemBuilder: (context, index) {{
          return _buildGridItem(index);
        }},
      ),
    );
  }}

  Widget _buildGridItem(int index) {{
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.image, size: 48, color: Colors.grey[400]),
          const SizedBox(height: 8),
          Text('Item ${{index + 1}}'),
        ],
      ),
    );
  }}
}}
'''

    def _tabs_layout(self, screen_name: str, metadata: Dict) -> str:
        """Generate tabs layout."""
        tabs = metadata.get("tabs", ["Tab 1", "Tab 2", "Tab 3"])
        return f'''import 'package:flutter/material.dart';

class {screen_name}Layout extends StatelessWidget {{
  const {screen_name}Layout({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return DefaultTabController(
      length: {len(tabs)},
      child: Scaffold(
        appBar: AppBar(
          title: const Text('{screen_name}'),
          bottom: TabBar(
            tabs: const [
{chr(10).join([f"              Tab(text: '{tab}')," for tab in tabs])}
            ],
          ),
        ),
        body: TabBarView(
          children: [
{chr(10).join([f"            _buildTab{i+1}Content()," for i in range(len(tabs))])}
          ],
        ),
      ),
    );
  }}

{chr(10).join([f'''  Widget _buildTab{i+1}Content() {{
    return const Center(child: Text('{tabs[i]} Content'));
  }}
''' for i in range(len(tabs))])}
}}
'''

    def _drawer_layout(self, screen_name: str, metadata: Dict) -> str:
        """Generate drawer layout."""
        return f'''import 'package:flutter/material.dart';

class {screen_name}Layout extends StatelessWidget {{
  const {screen_name}Layout({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{screen_name}')),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Colors.blue),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  CircleAvatar(radius: 30, child: Icon(Icons.person)),
                  SizedBox(height: 8),
                  Text('User Name', style: TextStyle(color: Colors.white)),
                ],
              ),
            ),
            ListTile(
              leading: const Icon(Icons.home),
              title: const Text('Home'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('Settings'),
              onTap: () => Navigator.pop(context),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Logout'),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
      body: const Center(child: Text('Main Content')),
    );
  }}
}}
'''

    async def _create_design_system(self, task: Task) -> Dict[str, Any]:
        """Create design system."""
        self.log("Creating design system")
        
        self.design_system = {
            "colors": self._generate_color_palette(),
            "typography": self._generate_typography(),
            "spacing": self._generate_spacing_scale(),
            "components": self._generate_component_specs(),
        }
        
        theme_code = self._generate_theme_code()
        
        return {
            "design_system": self.design_system,
            "theme_code": theme_code,
        }

    def _generate_color_palette(self) -> Dict[str, str]:
        """Generate color palette."""
        return {
            "primary": "#2196F3",
            "primaryLight": "#64B5F6",
            "primaryDark": "#1976D2",
            "secondary": "#FF9800",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "error": "#F44336",
            "background": "#FAFAFA",
            "surface": "#FFFFFF",
            "textPrimary": "#212121",
            "textSecondary": "#757575",
        }

    def _generate_typography(self) -> Dict[str, Dict]:
        """Generate typography scale."""
        return {
            "h1": {"size": 32, "weight": "bold", "height": 1.2},
            "h2": {"size": 28, "weight": "bold", "height": 1.25},
            "h3": {"size": 24, "weight": "semibold", "height": 1.3},
            "h4": {"size": 20, "weight": "semibold", "height": 1.35},
            "body1": {"size": 16, "weight": "normal", "height": 1.5},
            "body2": {"size": 14, "weight": "normal", "height": 1.5},
            "caption": {"size": 12, "weight": "normal", "height": 1.4},
            "button": {"size": 14, "weight": "medium", "height": 1.2},
        }

    def _generate_spacing_scale(self) -> Dict[str, int]:
        """Generate spacing scale."""
        return {
            "xs": 4,
            "sm": 8,
            "md": 16,
            "lg": 24,
            "xl": 32,
            "xxl": 48,
        }

    def _generate_component_specs(self) -> Dict[str, Dict]:
        """Generate component specifications."""
        return {
            "button": {
                "height": 48,
                "borderRadius": 8,
                "padding": {"horizontal": 24, "vertical": 12},
            },
            "input": {
                "height": 56,
                "borderRadius": 8,
                "padding": {"horizontal": 16, "vertical": 16},
            },
            "card": {
                "borderRadius": 12,
                "padding": 16,
                "elevation": 2,
            },
        }

    def _generate_theme_code(self) -> str:
        """Generate Flutter theme code."""
        return '''import 'package:flutter/material.dart';

class AppTheme {
  // Colors
  static const Color primary = Color(0xFF2196F3);
  static const Color primaryLight = Color(0xFF64B5F6);
  static const Color primaryDark = Color(0xFF1976D2);
  static const Color secondary = Color(0xFFFF9800);
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFFC107);
  static const Color error = Color(0xFFF44336);
  static const Color background = Color(0xFFFAFAFA);
  static const Color surface = Color(0xFFFFFFFF);
  
  // Spacing
  static const double spacingXs = 4;
  static const double spacingSm = 8;
  static const double spacingMd = 16;
  static const double spacingLg = 24;
  static const double spacingXl = 32;
  
  // Border Radius
  static const double radiusSm = 4;
  static const double radiusMd = 8;
  static const double radiusLg = 12;
  static const double radiusXl = 16;
  
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: background,
      appBarTheme: const AppBarTheme(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radiusMd),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: BorderSide(color: Colors.grey[300]!),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: BorderSide(color: Colors.grey[300]!),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusMd),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: spacingMd,
          vertical: spacingMd,
        ),
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusLg),
        ),
      ),
    );
  }
  
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        brightness: Brightness.dark,
      ),
      scaffoldBackgroundColor: const Color(0xFF121212),
    );
  }
}
'''

    async def _design_interaction(self, task: Task) -> Dict[str, Any]:
        """Design interaction patterns."""
        interaction_type = task.metadata.get("interaction_type", "button")
        
        self.log(f"Designing interaction: {interaction_type}")
        
        interaction_code = self._generate_interaction_code(interaction_type)
        
        return {
            "type": interaction_type,
            "code": interaction_code,
        }

    def _generate_interaction_code(self, interaction_type: str) -> str:
        """Generate interaction code."""
        return '''import 'package:flutter/material.dart';

/// Animated button with ripple and scale effects
class InteractiveButton extends StatefulWidget {
  final String label;
  final VoidCallback onPressed;
  final bool isLoading;

  const InteractiveButton({
    Key? key,
    required this.label,
    required this.onPressed,
    this.isLoading = false,
  }) : super(key: key);

  @override
  State<InteractiveButton> createState() => _InteractiveButtonState();
}

class _InteractiveButtonState extends State<InteractiveButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 100),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.95).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) {
        _controller.reverse();
        widget.onPressed();
      },
      onTapCancel: () => _controller.reverse(),
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          decoration: BoxDecoration(
            color: Theme.of(context).primaryColor,
            borderRadius: BorderRadius.circular(8),
            boxShadow: [
              BoxShadow(
                color: Theme.of(context).primaryColor.withOpacity(0.3),
                blurRadius: 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: widget.isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : Text(
                  widget.label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
        ),
      ),
    );
  }
}

/// Animated notification toast
class AnimatedToast extends StatefulWidget {
  final String message;
  final ToastType type;
  
  const AnimatedToast({
    Key? key,
    required this.message,
    this.type = ToastType.info,
  }) : super(key: key);

  @override
  State<AnimatedToast> createState() => _AnimatedToastState();
}

enum ToastType { success, error, warning, info }

class _AnimatedToastState extends State<AnimatedToast>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, -1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(_controller);
    
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color get _backgroundColor {
    switch (widget.type) {
      case ToastType.success:
        return Colors.green;
      case ToastType.error:
        return Colors.red;
      case ToastType.warning:
        return Colors.orange;
      case ToastType.info:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: _backgroundColor,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            widget.message,
            style: const TextStyle(color: Colors.white),
          ),
        ),
      ),
    );
  }
}
'''

    async def _implement_responsive(self, task: Task) -> Dict[str, Any]:
        """Implement responsive design."""
        breakpoints = task.metadata.get("breakpoints", {
            "mobile": 600,
            "tablet": 900,
            "desktop": 1200,
        })
        
        self.log("Implementing responsive design")
        
        responsive_code = self._generate_responsive_code(breakpoints)
        
        return {
            "breakpoints": breakpoints,
            "code": responsive_code,
        }

    def _generate_responsive_code(self, breakpoints: Dict[str, int]) -> str:
        """Generate responsive design utilities."""
        return f'''import 'package:flutter/material.dart';

/// Responsive breakpoints
class Breakpoints {{
  static const double mobile = {breakpoints.get('mobile', 600)};
  static const double tablet = {breakpoints.get('tablet', 900)};
  static const double desktop = {breakpoints.get('desktop', 1200)};
}}

/// Responsive builder widget
class ResponsiveBuilder extends StatelessWidget {{
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;

  const ResponsiveBuilder({{
    Key? key,
    required this.mobile,
    this.tablet,
    this.desktop,
  }}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return LayoutBuilder(
      builder: (context, constraints) {{
        if (constraints.maxWidth >= Breakpoints.desktop) {{
          return desktop ?? tablet ?? mobile;
        }}
        if (constraints.maxWidth >= Breakpoints.tablet) {{
          return tablet ?? mobile;
        }}
        return mobile;
      }},
    );
  }}
}}

/// Responsive extensions
extension ResponsiveExtension on BuildContext {{
  bool get isMobile => MediaQuery.of(this).size.width < Breakpoints.tablet;
  bool get isTablet => 
      MediaQuery.of(this).size.width >= Breakpoints.tablet &&
      MediaQuery.of(this).size.width < Breakpoints.desktop;
  bool get isDesktop => MediaQuery.of(this).size.width >= Breakpoints.desktop;
  
  double get screenWidth => MediaQuery.of(this).size.width;
  double get screenHeight => MediaQuery.of(this).size.height;
  
  EdgeInsets get responsivePadding {{
    if (isDesktop) return const EdgeInsets.all(32);
    if (isTablet) return const EdgeInsets.all(24);
    return const EdgeInsets.all(16);
  }}
  
  int get gridColumns {{
    if (isDesktop) return 4;
    if (isTablet) return 3;
    return 2;
  }}
}}

/// Responsive value helper
T responsiveValue<T>(
  BuildContext context, {{
  required T mobile,
  T? tablet,
  T? desktop,
}}) {{
  if (context.isDesktop) return desktop ?? tablet ?? mobile;
  if (context.isTablet) return tablet ?? mobile;
  return mobile;
}}
'''

    async def _ensure_accessibility(self, task: Task) -> Dict[str, Any]:
        """Ensure accessibility compliance."""
        self.log("Implementing accessibility features")
        
        guidelines = self._generate_accessibility_guidelines()
        code = self._generate_accessibility_code()
        
        return {
            "guidelines": guidelines,
            "code": code,
        }

    def _generate_accessibility_guidelines(self) -> List[str]:
        """Generate accessibility guidelines."""
        return [
            "Ensure minimum touch target size of 48x48 dp",
            "Maintain color contrast ratio of at least 4.5:1",
            "Provide semantic labels for all interactive elements",
            "Support dynamic text scaling",
            "Ensure proper focus order for screen readers",
            "Provide alternative text for images",
            "Support high contrast mode",
        ]

    def _generate_accessibility_code(self) -> str:
        """Generate accessibility helper code."""
        return '''import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';

/// Accessible Button wrapper
class AccessibleButton extends StatelessWidget {
  final String label;
  final String? hint;
  final VoidCallback onPressed;
  final Widget child;

  const AccessibleButton({
    Key? key,
    required this.label,
    this.hint,
    required this.onPressed,
    required this.child,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: label,
      hint: hint,
      button: true,
      child: InkWell(
        onTap: onPressed,
        child: Container(
          constraints: const BoxConstraints(
            minWidth: 48,
            minHeight: 48,
          ),
          child: child,
        ),
      ),
    );
  }
}

/// Accessible image with fallback
class AccessibleImage extends StatelessWidget {
  final String src;
  final String semanticLabel;
  final double? width;
  final double? height;

  const AccessibleImage({
    Key? key,
    required this.src,
    required this.semanticLabel,
    this.width,
    this.height,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Semantics(
      image: true,
      label: semanticLabel,
      child: Image.network(
        src,
        width: width,
        height: height,
        semanticLabel: semanticLabel,
        errorBuilder: (context, error, stackTrace) {
          return Container(
            width: width,
            height: height,
            color: Colors.grey[200],
            child: Icon(
              Icons.image_not_supported,
              semanticLabel: 'Image failed to load: $semanticLabel',
            ),
          );
        },
      ),
    );
  }
}

/// Check color contrast ratio
double calculateContrastRatio(Color foreground, Color background) {
  double l1 = _relativeLuminance(foreground);
  double l2 = _relativeLuminance(background);
  
  if (l1 > l2) {
    return (l1 + 0.05) / (l2 + 0.05);
  }
  return (l2 + 0.05) / (l1 + 0.05);
}

double _relativeLuminance(Color color) {
  double r = _linearize(color.red / 255);
  double g = _linearize(color.green / 255);
  double b = _linearize(color.blue / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

double _linearize(double value) {
  if (value <= 0.03928) {
    return value / 12.92;
  }
  return ((value + 0.055) / 1.055).pow(2.4);
}
'''

    async def _create_component(self, task: Task) -> Dict[str, Any]:
        """Create reusable UI component."""
        component_name = task.metadata.get("component_name", "Component")
        component_type = task.metadata.get("component_type", "card")
        
        self.log(f"Creating component: {component_name}")
        
        component_code = self._generate_component_code(component_name, component_type)
        
        component = {
            "name": component_name,
            "type": component_type,
            "code": component_code,
        }
        self.components.append(component)
        
        return component

    def _generate_component_code(self, name: str, component_type: str) -> str:
        """Generate component code."""
        return f'''import 'package:flutter/material.dart';

class {name} extends StatelessWidget {{
  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final VoidCallback? onTap;

  const {name}({{
    Key? key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.onTap,
  }}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              if (leading != null) ...[
                leading!,
                const SizedBox(width: 16),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    if (subtitle != null)
                      Text(
                        subtitle!,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                  ],
                ),
              ),
              if (trailing != null) trailing!,
            ],
          ),
        ),
      ),
    );
  }}
}}
'''

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic UI/UX tasks."""
        self.log(f"Handling generic UI/UX task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic UI/UX task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with UI/UX-specific info."""
        base_status = super().get_status()
        base_status.update({
            "wireframes": len(self.wireframes),
            "components": len(self.components),
            "has_design_system": bool(self.design_system),
        })
        return base_status
