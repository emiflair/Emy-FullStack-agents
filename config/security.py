"""
Security Configuration
Authentication, encryption, and security settings
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import timedelta
import os
import secrets


class AuthMethod(str, Enum):
    """Authentication methods"""
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class EncryptionAlgorithm(str, Enum):
    """Encryption algorithms"""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"


class HashAlgorithm(str, Enum):
    """Hashing algorithms"""
    BCRYPT = "bcrypt"
    ARGON2 = "argon2"
    SCRYPT = "scrypt"
    SHA256 = "sha256"


@dataclass
class JWTConfig:
    """JWT configuration"""
    secret_key: str = field(
        default_factory=lambda: os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: str = "emy-fullstack"
    audience: str = "emy-fullstack-api"
    
    @property
    def access_token_lifetime(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)
    
    @property
    def refresh_token_lifetime(self) -> timedelta:
        return timedelta(days=self.refresh_token_expire_days)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm,
            'access_token_expire_minutes': self.access_token_expire_minutes,
            'refresh_token_expire_days': self.refresh_token_expire_days,
            'issuer': self.issuer,
            'audience': self.audience,
        }


@dataclass
class OAuth2Config:
    """OAuth2 configuration"""
    client_id: Optional[str] = field(
        default_factory=lambda: os.getenv('OAUTH2_CLIENT_ID')
    )
    client_secret: Optional[str] = field(
        default_factory=lambda: os.getenv('OAUTH2_CLIENT_SECRET')
    )
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    redirect_uri: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'client_id': self.client_id,
            'authorization_url': self.authorization_url,
            'token_url': self.token_url,
            'redirect_uri': self.redirect_uri,
            'scopes': self.scopes,
        }


@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key: str = field(
        default_factory=lambda: os.getenv('ENCRYPTION_KEY', secrets.token_hex(32))
    )
    iv_length: int = 12  # bytes
    tag_length: int = 16  # bytes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm.value,
            'iv_length': self.iv_length,
            'tag_length': self.tag_length,
        }


@dataclass
class PasswordConfig:
    """Password hashing configuration"""
    algorithm: HashAlgorithm = HashAlgorithm.BCRYPT
    bcrypt_rounds: int = 12
    argon2_memory_cost: int = 65536
    argon2_time_cost: int = 3
    argon2_parallelism: int = 4
    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm.value,
            'min_length': self.min_length,
            'require_uppercase': self.require_uppercase,
            'require_lowercase': self.require_lowercase,
            'require_digit': self.require_digit,
            'require_special': self.require_special,
        }


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    default_limit: int = 100  # requests
    default_window: int = 60  # seconds
    burst_limit: int = 20
    
    # Endpoint-specific limits
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.endpoint_limits:
            self.endpoint_limits = {
                '/auth/login': {'limit': 10, 'window': 60},
                '/auth/register': {'limit': 5, 'window': 60},
                '/api/generate': {'limit': 20, 'window': 60},
            }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'default_limit': self.default_limit,
            'default_window': self.default_window,
            'burst_limit': self.burst_limit,
            'endpoint_limits': self.endpoint_limits,
        }


@dataclass
class CORSConfig:
    """CORS configuration"""
    enabled: bool = True
    allow_origins: List[str] = field(
        default_factory=lambda: os.getenv(
            'CORS_ORIGINS', 
            'http://localhost:3000,http://localhost:8080'
        ).split(',')
    )
    allow_methods: List[str] = field(
        default_factory=lambda: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
    )
    allow_headers: List[str] = field(
        default_factory=lambda: ['*']
    )
    allow_credentials: bool = True
    max_age: int = 600  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'allow_origins': self.allow_origins,
            'allow_methods': self.allow_methods,
            'allow_headers': self.allow_headers,
            'allow_credentials': self.allow_credentials,
            'max_age': self.max_age,
        }


@dataclass
class SecurityConfig:
    """Main security configuration"""
    auth_method: AuthMethod = AuthMethod.JWT
    jwt: JWTConfig = field(default_factory=JWTConfig)
    oauth2: OAuth2Config = field(default_factory=OAuth2Config)
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
    password: PasswordConfig = field(default_factory=PasswordConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    
    # Security headers
    security_headers: Dict[str, str] = field(default_factory=dict)
    
    # Session settings
    session_cookie_name: str = "session"
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    
    # API key settings
    api_key_header: str = "X-API-Key"
    api_key_query_param: str = "api_key"
    
    def __post_init__(self):
        if not self.security_headers:
            self.security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': "default-src 'self'",
                'Referrer-Policy': 'strict-origin-when-cross-origin',
            }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'auth_method': self.auth_method.value,
            'jwt': self.jwt.to_dict(),
            'oauth2': self.oauth2.to_dict(),
            'encryption': self.encryption.to_dict(),
            'password': self.password.to_dict(),
            'rate_limit': self.rate_limit.to_dict(),
            'cors': self.cors.to_dict(),
            'security_headers': self.security_headers,
        }


# Role-based access control
RBAC_ROLES = {
    'admin': {
        'permissions': ['*'],
        'description': 'Full system access',
    },
    'developer': {
        'permissions': [
            'agents:read',
            'agents:execute',
            'tasks:read',
            'tasks:create',
            'tasks:update',
            'projects:read',
            'projects:create',
        ],
        'description': 'Developer access',
    },
    'viewer': {
        'permissions': [
            'agents:read',
            'tasks:read',
            'projects:read',
        ],
        'description': 'Read-only access',
    },
    'agent': {
        'permissions': [
            'tasks:read',
            'tasks:update',
            'logs:create',
        ],
        'description': 'Agent execution access',
    },
}


# Audit log configuration
AUDIT_CONFIG = {
    'enabled': True,
    'log_level': 'INFO',
    'include_request_body': False,
    'include_response_body': False,
    'exclude_paths': ['/health', '/metrics'],
    'retention_days': 90,
}


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return SecurityConfig()
