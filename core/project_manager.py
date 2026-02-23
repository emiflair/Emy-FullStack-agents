"""
Project Creator
Creates full project scaffolds with all necessary files and structure
"""

import os
import json
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """Types of projects that can be created"""
    FLUTTER_MOBILE = "flutter_mobile"
    FLUTTER_WEB = "flutter_web"
    FLUTTER_FULL = "flutter_full"  # Mobile + Web
    FASTAPI_BACKEND = "fastapi_backend"
    FULLSTACK = "fullstack"  # Flutter + FastAPI
    MICROSERVICES = "microservices"


class DatabaseType(Enum):
    """Database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    NONE = "none"


class AuthType(Enum):
    """Authentication types"""
    JWT = "jwt"
    OAUTH2 = "oauth2"
    FIREBASE = "firebase"
    NONE = "none"


@dataclass
class ProjectConfig:
    """Configuration for a new project"""
    name: str
    description: str
    project_type: ProjectType = ProjectType.FULLSTACK
    database: DatabaseType = DatabaseType.POSTGRESQL
    auth: AuthType = AuthType.JWT
    
    # Features
    features: List[str] = field(default_factory=lambda: [
        "user_auth",
        "api_endpoints",
        "database",
        "docker",
    ])
    
    # Technology choices
    state_management: str = "riverpod"  # riverpod, provider, bloc
    api_style: str = "rest"  # rest, graphql
    
    # Paths
    output_path: Optional[str] = None
    
    # Additional config
    include_tests: bool = True
    include_docker: bool = True
    include_ci_cd: bool = True
    include_docs: bool = True
    
    # API keys and external services
    use_openai: bool = True
    use_firebase: bool = False
    use_stripe: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'project_type': self.project_type.value,
            'database': self.database.value,
            'auth': self.auth.value,
            'features': self.features,
            'state_management': self.state_management,
            'api_style': self.api_style,
        }


class ProjectCreator:
    """
    Creates complete project scaffolds
    Generates directory structure, boilerplate, and configuration files
    """
    
    def __init__(self, ai_generator=None):
        self.ai_generator = ai_generator
        self._created_files: List[str] = []
    
    def create_project(self, config: ProjectConfig) -> Dict[str, Any]:
        """Create a complete project based on configuration"""
        output_path = Path(config.output_path or f"./{config.name}")
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating project: {config.name} at {output_path}")
        
        result = {
            'name': config.name,
            'path': str(output_path),
            'files_created': [],
            'structure': {},
        }
        
        # Create based on project type
        if config.project_type in [ProjectType.FLUTTER_MOBILE, ProjectType.FLUTTER_WEB, ProjectType.FLUTTER_FULL]:
            self._create_flutter_project(output_path, config)
        
        elif config.project_type == ProjectType.FASTAPI_BACKEND:
            self._create_fastapi_project(output_path, config)
        
        elif config.project_type == ProjectType.FULLSTACK:
            self._create_fullstack_project(output_path, config)
        
        elif config.project_type == ProjectType.MICROSERVICES:
            self._create_microservices_project(output_path, config)
        
        result['files_created'] = self._created_files.copy()
        result['structure'] = self._get_directory_structure(output_path)
        self._created_files.clear()
        
        logger.info(f"Project created: {len(result['files_created'])} files")
        return result
    
    def _create_file(self, path: Path, content: str):
        """Create a file with content"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self._created_files.append(str(path))
    
    def _get_directory_structure(self, path: Path, prefix: str = "") -> Dict[str, Any]:
        """Get directory structure as dict"""
        structure = {}
        for item in sorted(path.iterdir()):
            if item.name.startswith('.') and item.name not in ['.env.example', '.gitignore']:
                continue
            if item.is_dir():
                structure[item.name + "/"] = self._get_directory_structure(item)
            else:
                structure[item.name] = None
        return structure
    
    # ==================== Flutter Project ====================
    
    def _create_flutter_project(self, path: Path, config: ProjectConfig):
        """Create Flutter project structure"""
        # pubspec.yaml
        self._create_file(path / "pubspec.yaml", self._flutter_pubspec(config))
        
        # Main entry point
        self._create_file(path / "lib" / "main.dart", self._flutter_main(config))
        
        # App configuration
        self._create_file(path / "lib" / "app" / "app.dart", self._flutter_app(config))
        self._create_file(path / "lib" / "app" / "router.dart", self._flutter_router(config))
        self._create_file(path / "lib" / "app" / "theme.dart", self._flutter_theme(config))
        
        # Core
        self._create_file(path / "lib" / "core" / "constants.dart", self._flutter_constants(config))
        self._create_file(path / "lib" / "core" / "api_client.dart", self._flutter_api_client(config))
        self._create_file(path / "lib" / "core" / "storage.dart", self._flutter_storage(config))
        
        # Features - Auth
        if "user_auth" in config.features:
            self._create_file(path / "lib" / "features" / "auth" / "auth_provider.dart", 
                            self._flutter_auth_provider(config))
            self._create_file(path / "lib" / "features" / "auth" / "login_screen.dart",
                            self._flutter_login_screen(config))
            self._create_file(path / "lib" / "features" / "auth" / "register_screen.dart",
                            self._flutter_register_screen(config))
        
        # Features - Home
        self._create_file(path / "lib" / "features" / "home" / "home_screen.dart",
                        self._flutter_home_screen(config))
        
        # Models
        self._create_file(path / "lib" / "models" / "user.dart", self._flutter_user_model(config))
        
        # Tests
        if config.include_tests:
            self._create_file(path / "test" / "widget_test.dart", self._flutter_widget_test(config))
        
        # Analysis options
        self._create_file(path / "analysis_options.yaml", self._flutter_analysis_options())
    
    def _flutter_pubspec(self, config: ProjectConfig) -> str:
        return f'''name: {config.name.lower().replace('-', '_').replace(' ', '_')}
description: {config.description}
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_riverpod: ^2.4.9
  riverpod_annotation: ^2.3.3
  
  # Navigation
  go_router: ^13.0.0
  
  # Networking
  dio: ^5.4.0
  
  # Local Storage
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  
  # UI
  google_fonts: ^6.1.0
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.1
  
  # Utils
  intl: ^0.19.0
  logger: ^2.0.2
  json_annotation: ^4.8.1
  freezed_annotation: ^2.4.1
  equatable: ^2.0.5

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1
  build_runner: ^2.4.8
  json_serializable: ^6.7.1
  freezed: ^2.4.6
  riverpod_generator: ^2.3.9
  mockito: ^5.4.4
  bloc_test: ^9.1.5

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/icons/
'''
    
    def _flutter_main(self, config: ProjectConfig) -> str:
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';

void main() {{
  WidgetsFlutterBinding.ensureInitialized();
  
  runApp(
    const ProviderScope(
      child: App(),
    ),
  );
}}
'''
    
    def _flutter_app(self, config: ProjectConfig) -> str:
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'router.dart';
import 'theme.dart';

class App extends ConsumerWidget {{
  const App({{super.key}});

  @override
  Widget build(BuildContext context, WidgetRef ref) {{
    final router = ref.watch(routerProvider);
    
    return MaterialApp.router(
      title: '{config.name}',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }}
}}
'''
    
    def _flutter_router(self, config: ProjectConfig) -> str:
        routes = '''
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),''' if "user_auth" in config.features else ""
        
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/home/home_screen.dart';
{"import '../features/auth/login_screen.dart';" if "user_auth" in config.features else ""}
{"import '../features/auth/register_screen.dart';" if "user_auth" in config.features else ""}

final routerProvider = Provider<GoRouter>((ref) {{
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),{routes}
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${{state.uri}}'),
      ),
    ),
  );
}});
'''
    
    def _flutter_theme(self, config: ProjectConfig) -> str:
        return '''import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: Colors.blue,
        brightness: Brightness.light,
      ),
      textTheme: GoogleFonts.interTextTheme(),
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    );
  }
  
  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: Colors.blue,
        brightness: Brightness.dark,
      ),
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
      ),
    );
  }
}
'''
    
    def _flutter_constants(self, config: ProjectConfig) -> str:
        return f'''class AppConstants {{
  static const String appName = '{config.name}';
  static const String apiBaseUrl = 'http://localhost:8000/api/v1';
  
  // API Endpoints
  static const String loginEndpoint = '/auth/login';
  static const String registerEndpoint = '/auth/register';
  static const String refreshTokenEndpoint = '/auth/refresh';
  static const String userProfileEndpoint = '/users/me';
  
  // Storage Keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userKey = 'user';
  
  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
}}
'''
    
    def _flutter_api_client(self, config: ProjectConfig) -> str:
        return '''import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'constants.dart';
import 'storage.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(storageProvider);
  return ApiClient(storage: storage);
});

class ApiClient {
  final Storage storage;
  late final Dio _dio;
  
  ApiClient({required this.storage}) {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: AppConstants.connectionTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));
    
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await storage.getAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Handle token refresh
          final refreshed = await _refreshToken();
          if (refreshed) {
            // Retry original request
            final response = await _dio.fetch(error.requestOptions);
            handler.resolve(response);
            return;
          }
        }
        handler.next(error);
      },
    ));
  }
  
  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await storage.getRefreshToken();
      if (refreshToken == null) return false;
      
      final response = await _dio.post(
        AppConstants.refreshTokenEndpoint,
        data: {'refresh_token': refreshToken},
      );
      
      await storage.saveTokens(
        accessToken: response.data['access_token'],
        refreshToken: response.data['refresh_token'],
      );
      
      return true;
    } catch (e) {
      await storage.clearTokens();
      return false;
    }
  }
  
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters}) {
    return _dio.get<T>(path, queryParameters: queryParameters);
  }
  
  Future<Response<T>> post<T>(String path, {dynamic data}) {
    return _dio.post<T>(path, data: data);
  }
  
  Future<Response<T>> put<T>(String path, {dynamic data}) {
    return _dio.put<T>(path, data: data);
  }
  
  Future<Response<T>> delete<T>(String path) {
    return _dio.delete<T>(path);
  }
}
'''
    
    def _flutter_storage(self, config: ProjectConfig) -> str:
        return '''import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'constants.dart';

final storageProvider = Provider<Storage>((ref) {
  return Storage();
});

class Storage {
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  SharedPreferences? _prefs;
  
  Future<SharedPreferences> get prefs async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }
  
  // Token Management
  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _secureStorage.write(key: AppConstants.accessTokenKey, value: accessToken);
    await _secureStorage.write(key: AppConstants.refreshTokenKey, value: refreshToken);
  }
  
  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: AppConstants.accessTokenKey);
  }
  
  Future<String?> getRefreshToken() async {
    return await _secureStorage.read(key: AppConstants.refreshTokenKey);
  }
  
  Future<void> clearTokens() async {
    await _secureStorage.delete(key: AppConstants.accessTokenKey);
    await _secureStorage.delete(key: AppConstants.refreshTokenKey);
  }
  
  // General Storage
  Future<void> setString(String key, String value) async {
    final p = await prefs;
    await p.setString(key, value);
  }
  
  Future<String?> getString(String key) async {
    final p = await prefs;
    return p.getString(key);
  }
  
  Future<void> setBool(String key, bool value) async {
    final p = await prefs;
    await p.setBool(key, value);
  }
  
  Future<bool?> getBool(String key) async {
    final p = await prefs;
    return p.getBool(key);
  }
  
  Future<void> remove(String key) async {
    final p = await prefs;
    await p.remove(key);
  }
  
  Future<void> clear() async {
    final p = await prefs;
    await p.clear();
    await _secureStorage.deleteAll();
  }
}
'''
    
    def _flutter_auth_provider(self, config: ProjectConfig) -> str:
        return '''import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/storage.dart';
import '../../core/constants.dart';
import '../../models/user.dart';

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(
    apiClient: ref.watch(apiClientProvider),
    storage: ref.watch(storageProvider),
  );
});

class AuthState {
  final User? user;
  final bool isLoading;
  final String? error;
  final bool isAuthenticated;
  
  AuthState({
    this.user,
    this.isLoading = false,
    this.error,
    this.isAuthenticated = false,
  });
  
  AuthState copyWith({
    User? user,
    bool? isLoading,
    String? error,
    bool? isAuthenticated,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient apiClient;
  final Storage storage;
  
  AuthNotifier({
    required this.apiClient,
    required this.storage,
  }) : super(AuthState()) {
    _checkAuthStatus();
  }
  
  Future<void> _checkAuthStatus() async {
    final token = await storage.getAccessToken();
    if (token != null) {
      await fetchUser();
    }
  }
  
  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final response = await apiClient.post(
        AppConstants.loginEndpoint,
        data: {'email': email, 'password': password},
      );
      
      await storage.saveTokens(
        accessToken: response.data['access_token'],
        refreshToken: response.data['refresh_token'],
      );
      
      final user = User.fromJson(response.data['user']);
      state = state.copyWith(
        user: user,
        isLoading: false,
        isAuthenticated: true,
      );
      
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Login failed. Please check your credentials.',
      );
      return false;
    }
  }
  
  Future<bool> register(String name, String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final response = await apiClient.post(
        AppConstants.registerEndpoint,
        data: {'name': name, 'email': email, 'password': password},
      );
      
      await storage.saveTokens(
        accessToken: response.data['access_token'],
        refreshToken: response.data['refresh_token'],
      );
      
      final user = User.fromJson(response.data['user']);
      state = state.copyWith(
        user: user,
        isLoading: false,
        isAuthenticated: true,
      );
      
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Registration failed. Please try again.',
      );
      return false;
    }
  }
  
  Future<void> fetchUser() async {
    try {
      final response = await apiClient.get(AppConstants.userProfileEndpoint);
      final user = User.fromJson(response.data);
      state = state.copyWith(user: user, isAuthenticated: true);
    } catch (e) {
      await logout();
    }
  }
  
  Future<void> logout() async {
    await storage.clearTokens();
    state = AuthState();
  }
}
'''
    
    def _flutter_login_screen(self, config: ProjectConfig) -> str:
        return '''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_formKey.currentState?.validate() ?? false) {
      final success = await ref.read(authProvider.notifier).login(
        _emailController.text.trim(),
        _passwordController.text,
      );
      
      if (success && mounted) {
        context.go('/');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Welcome Back',
                  style: Theme.of(context).textTheme.headlineMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.email_outlined),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your email';
                    }
                    if (!value.contains('@')) {
                      return 'Please enter a valid email';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock_outlined),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword ? Icons.visibility : Icons.visibility_off,
                      ),
                      onPressed: () {
                        setState(() => _obscurePassword = !_obscurePassword);
                      },
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your password';
                    }
                    return null;
                  },
                ),
                if (authState.error != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    authState.error!,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: authState.isLoading ? null : _login,
                  child: authState.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Login'),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () => context.go('/register'),
                  child: const Text("Don't have an account? Register"),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
'''
    
    def _flutter_register_screen(self, config: ProjectConfig) -> str:
        return '''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'auth_provider.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if (_formKey.currentState?.validate() ?? false) {
      final success = await ref.read(authProvider.notifier).register(
        _nameController.text.trim(),
        _emailController.text.trim(),
        _passwordController.text,
      );
      
      if (success && mounted) {
        context.go('/');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    
    return Scaffold(
      appBar: AppBar(title: const Text('Register')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Create Account',
                  style: Theme.of(context).textTheme.headlineMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Full Name',
                    prefixIcon: Icon(Icons.person_outlined),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your name';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.email_outlined),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your email';
                    }
                    if (!value.contains('@')) {
                      return 'Please enter a valid email';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock_outlined),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword ? Icons.visibility : Icons.visibility_off,
                      ),
                      onPressed: () {
                        setState(() => _obscurePassword = !_obscurePassword);
                      },
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter a password';
                    }
                    if (value.length < 8) {
                      return 'Password must be at least 8 characters';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _confirmPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Confirm Password',
                    prefixIcon: Icon(Icons.lock_outlined),
                  ),
                  validator: (value) {
                    if (value != _passwordController.text) {
                      return 'Passwords do not match';
                    }
                    return null;
                  },
                ),
                if (authState.error != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    authState.error!,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: authState.isLoading ? null : _register,
                  child: authState.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Register'),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () => context.go('/login'),
                  child: const Text('Already have an account? Login'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
'''
    
    def _flutter_home_screen(self, config: ProjectConfig) -> str:
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
{"import '../auth/auth_provider.dart';" if "user_auth" in config.features else ""}

class HomeScreen extends ConsumerWidget {{
  const HomeScreen({{super.key}});

  @override
  Widget build(BuildContext context, WidgetRef ref) {{
    {"final authState = ref.watch(authProvider);" if "user_auth" in config.features else ""}
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('{config.name}'),
        actions: [
          {"IconButton(" if "user_auth" in config.features else ""}
          {"  icon: const Icon(Icons.logout)," if "user_auth" in config.features else ""}
          {"  onPressed: () => ref.read(authProvider.notifier).logout()," if "user_auth" in config.features else ""}
          {")," if "user_auth" in config.features else ""}
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.rocket_launch,
              size: 80,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'Welcome to {config.name}!',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              '{config.description}',
              style: Theme.of(context).textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
            {"const SizedBox(height: 24)," if "user_auth" in config.features else ""}
            {"if (authState.user != null)" if "user_auth" in config.features else ""}
            {"  Text('Logged in as: \\${{authState.user!.email}}')," if "user_auth" in config.features else ""}
          ],
        ),
      ),
    );
  }}
}}
'''
    
    def _flutter_user_model(self, config: ProjectConfig) -> str:
        return '''import 'package:equatable/equatable.dart';

class User extends Equatable {
  final String id;
  final String name;
  final String email;
  final String? avatarUrl;
  final DateTime createdAt;
  final DateTime? updatedAt;

  const User({
    required this.id,
    required this.name,
    required this.email,
    this.avatarUrl,
    required this.createdAt,
    this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      avatarUrl: json['avatar_url'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at'] as String) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'avatar_url': avatarUrl,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  User copyWith({
    String? id,
    String? name,
    String? email,
    String? avatarUrl,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return User(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [id, name, email, avatarUrl, createdAt, updatedAt];
}
'''
    
    def _flutter_widget_test(self, config: ProjectConfig) -> str:
        return f'''import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {{
  testWidgets('App renders correctly', (WidgetTester tester) async {{
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Center(child: Text('{config.name}')),
          ),
        ),
      ),
    );

    expect(find.text('{config.name}'), findsOneWidget);
  }});
}}
'''
    
    def _flutter_analysis_options(self) -> str:
        return '''include: package:flutter_lints/flutter.yaml

linter:
  rules:
    - prefer_const_constructors
    - prefer_const_declarations
    - prefer_final_fields
    - prefer_final_locals
    - avoid_print
    - require_trailing_commas

analyzer:
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
'''

    # ==================== FastAPI Project ====================
    
    def _create_fastapi_project(self, path: Path, config: ProjectConfig):
        """Create FastAPI project structure"""
        # Main entry
        self._create_file(path / "main.py", self._fastapi_main(config))
        
        # App module
        self._create_file(path / "app" / "__init__.py", "")
        self._create_file(path / "app" / "config.py", self._fastapi_config(config))
        self._create_file(path / "app" / "database.py", self._fastapi_database(config))
        
        # Models
        self._create_file(path / "app" / "models" / "__init__.py", "from .user import User")
        self._create_file(path / "app" / "models" / "user.py", self._fastapi_user_model(config))
        
        # Schemas
        self._create_file(path / "app" / "schemas" / "__init__.py", "from .user import *\nfrom .auth import *")
        self._create_file(path / "app" / "schemas" / "user.py", self._fastapi_user_schema(config))
        self._create_file(path / "app" / "schemas" / "auth.py", self._fastapi_auth_schema(config))
        
        # API routes
        self._create_file(path / "app" / "api" / "__init__.py", "")
        self._create_file(path / "app" / "api" / "router.py", self._fastapi_router(config))
        self._create_file(path / "app" / "api" / "auth.py", self._fastapi_auth_routes(config))
        self._create_file(path / "app" / "api" / "users.py", self._fastapi_users_routes(config))
        
        # Services
        self._create_file(path / "app" / "services" / "__init__.py", "")
        self._create_file(path / "app" / "services" / "auth_service.py", self._fastapi_auth_service(config))
        
        # Core
        self._create_file(path / "app" / "core" / "__init__.py", "")
        self._create_file(path / "app" / "core" / "security.py", self._fastapi_security(config))
        self._create_file(path / "app" / "core" / "deps.py", self._fastapi_deps(config))
        
        # Requirements
        self._create_file(path / "requirements.txt", self._fastapi_requirements(config))
        
        # Environment
        self._create_file(path / ".env.example", self._fastapi_env_example(config))
        
        # Docker
        if config.include_docker:
            self._create_file(path / "Dockerfile", self._fastapi_dockerfile(config))
            self._create_file(path / "docker-compose.yaml", self._fastapi_docker_compose(config))
        
        # Tests
        if config.include_tests:
            self._create_file(path / "tests" / "__init__.py", "")
            self._create_file(path / "tests" / "conftest.py", self._fastapi_conftest(config))
            self._create_file(path / "tests" / "test_auth.py", self._fastapi_test_auth(config))
        
        # Alembic migrations
        self._create_file(path / "alembic.ini", self._fastapi_alembic_ini(config))
        self._create_file(path / "alembic" / "env.py", self._fastapi_alembic_env(config))
        
        # README
        if config.include_docs:
            self._create_file(path / "README.md", self._fastapi_readme(config))
    
    def _fastapi_main(self, config: ProjectConfig) -> str:
        return f'''"""
{config.name} - FastAPI Backend
{config.description}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="{config.name}",
    description="{config.description}",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {{"status": "healthy", "version": "1.0.0"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
'''
    
    def _fastapi_config(self, config: ProjectConfig) -> str:
        return f'''from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    app_name: str = "{config.name}"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/{config.name.lower().replace(' ', '_')}"
    
    # JWT
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Redis (optional)
    redis_url: str = "redis://localhost:6379/0"
    
    {"# OpenAI" if config.use_openai else ""}
    {"openai_api_key: str = ''" if config.use_openai else ""}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
'''
    
    def _fastapi_database(self, config: ProjectConfig) -> str:
        return '''from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
'''
    
    def _fastapi_user_model(self, config: ProjectConfig) -> str:
        return '''from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email}>"
'''
    
    def _fastapi_user_schema(self, config: ProjectConfig) -> str:
        return '''from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    hashed_password: str
'''
    
    def _fastapi_auth_schema(self, config: ProjectConfig) -> str:
        return '''from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
'''
    
    def _fastapi_router(self, config: ProjectConfig) -> str:
        return '''from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
'''
    
    def _fastapi_auth_routes(self, config: ProjectConfig) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, AuthResponse, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user"""
    auth_service = AuthService(db)
    
    # Check if user exists
    existing_user = await auth_service.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = await auth_service.create_user(
        UserCreate(
            email=request.email,
            name=request.name,
            password=request.password,
        )
    )
    
    # Generate tokens
    tokens = auth_service.create_tokens(str(user.id))
    
    return AuthResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user).model_dump(),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login user"""
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    tokens = auth_service.create_tokens(str(user.id))
    
    return AuthResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user).model_dump(),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token"""
    auth_service = AuthService(db)
    
    try:
        tokens = await auth_service.refresh_tokens(request.refresh_token)
        return TokenResponse(**tokens)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
'''
    
    def _fastapi_users_routes(self, config: ProjectConfig) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile"""
    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user
'''
    
    def _fastapi_auth_service(self, config: ProjectConfig) -> str:
        return '''from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, user_create: UserCreate) -> User:
        user = User(
            email=user_create.email,
            name=user_create.name,
            hashed_password=self.hash_password(user_create.password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_tokens(self, user_id: str) -> dict:
        access_token = self._create_access_token(user_id)
        refresh_token = self._create_refresh_token(user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    
    def _create_access_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode = {"sub": user_id, "exp": expire, "type": "access"}
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def _create_refresh_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    async def refresh_tokens(self, refresh_token: str) -> dict:
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            
            user_id = payload.get("sub")
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            return self.create_tokens(user_id)
        except JWTError:
            raise ValueError("Invalid token")
'''
    
    def _fastapi_security(self, config: ProjectConfig) -> str:
        return '''from datetime import datetime
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, expected_type: str = "access") -> str:
    """Verify token and return user_id"""
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    exp = payload.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    return user_id
'''
    
    def _fastapi_deps(self, config: ProjectConfig) -> str:
        return '''from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.core.security import verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = verify_token(token)
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    
    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
'''
    
    def _fastapi_requirements(self, config: ProjectConfig) -> str:
        reqs = '''# FastAPI
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0

# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# HTTP Client
httpx>=0.26.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0

# Code Quality
black>=23.12.0
ruff>=0.1.0
mypy>=1.8.0
'''
        if config.use_openai:
            reqs += "\n# AI\nopenai>=1.6.0\n"
        
        return reqs
    
    def _fastapi_env_example(self, config: ProjectConfig) -> str:
        env = f'''# Application
APP_NAME={config.name}
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/{config.name.lower().replace(' ', '_')}

# JWT
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Redis
REDIS_URL=redis://localhost:6379/0
'''
        if config.use_openai:
            env += "\n# OpenAI\nOPENAI_API_KEY=sk-your-key-here\n"
        
        return env
    
    def _fastapi_dockerfile(self, config: ProjectConfig) -> str:
        return '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _fastapi_docker_compose(self, config: ProjectConfig) -> str:
        return f'''version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/{config.name.lower().replace(' ', '_')}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB={config.name.lower().replace(' ', '_')}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
'''
    
    def _fastapi_conftest(self, config: ProjectConfig) -> str:
        return '''import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from app.database import Base, get_db

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
'''
    
    def _fastapi_test_auth(self, config: ProjectConfig) -> str:
        return '''import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    
    # Try login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
'''
    
    def _fastapi_alembic_ini(self, config: ProjectConfig) -> str:
        return '''[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''
    
    def _fastapi_alembic_env(self, config: ProjectConfig) -> str:
        return '''import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.database import Base
from app.models import user  # Import all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    
    def _fastapi_readme(self, config: ProjectConfig) -> str:
        return f'''# {config.name}

{config.description}

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis (optional)

### Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn main:app --reload
```

### Using Docker

```bash
docker-compose up -d
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user

## Testing

```bash
pytest -v
```

## License

MIT
'''

    # ==================== Full Stack Project ====================
    
    def _create_fullstack_project(self, path: Path, config: ProjectConfig):
        """Create fullstack project with Flutter frontend and FastAPI backend"""
        # Create frontend
        frontend_path = path / "frontend"
        self._create_flutter_project(frontend_path, config)
        
        # Create backend
        backend_path = path / "backend"
        self._create_fastapi_project(backend_path, config)
        
        # Root files
        self._create_file(path / "README.md", self._fullstack_readme(config))
        self._create_file(path / "docker-compose.yaml", self._fullstack_docker_compose(config))
        self._create_file(path / "Makefile", self._fullstack_makefile(config))
        self._create_file(path / ".gitignore", self._fullstack_gitignore())
    
    def _fullstack_readme(self, config: ProjectConfig) -> str:
        return f'''# {config.name}

{config.description}

## Project Structure

```
{config.name}/
├── frontend/          # Flutter mobile/web app
├── backend/           # FastAPI REST API
├── docker-compose.yaml
└── Makefile
```

## Quick Start

### Using Makefile

```bash
# Start all services
make up

# Stop all services
make down

# View logs
make logs
```

### Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
flutter pub get
flutter run
```

## API Documentation

http://localhost:8000/docs

## License

MIT
'''
    
    def _fullstack_docker_compose(self, config: ProjectConfig) -> str:
        db_name = config.name.lower().replace(' ', '_').replace('-', '_')
        return f'''version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/{db_name}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB={db_name}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
'''
    
    def _fullstack_makefile(self, config: ProjectConfig) -> str:
        return '''# Development commands

.PHONY: up down logs backend frontend test

up:
\tdocker-compose up -d

down:
\tdocker-compose down

logs:
\tdocker-compose logs -f

backend:
\tcd backend && uvicorn main:app --reload

frontend:
\tcd frontend && flutter run

test:
\tcd backend && pytest -v

migrate:
\tcd backend && alembic upgrade head

clean:
\tdocker-compose down -v
\trm -rf backend/__pycache__ backend/.pytest_cache
'''
    
    def _fullstack_gitignore(self) -> str:
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
.env
venv/
.venv/
*.egg-info/
dist/
build/

# Flutter
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
.pub-cache/
.pub/
/build/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
*.db

# Logs
*.log
'''

    def _create_microservices_project(self, path: Path, config: ProjectConfig):
        """Create microservices architecture project"""
        # TODO: Implement microservices structure
        self._create_fullstack_project(path, config)
