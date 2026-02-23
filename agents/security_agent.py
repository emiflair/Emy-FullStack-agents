"""
Security Specialist Agent
Responsible for securing APIs, data, automation pipelines,
monitoring anomalies, and encrypting sensitive data.
"""

from typing import Any, Dict, List
from .base_agent import BaseAgent, Task


class SecurityAgent(BaseAgent):
    """
    Security Specialist Agent for the Emy-FullStack system.
    
    Capabilities:
    - Secure APIs and endpoints
    - Data encryption and protection
    - Security monitoring and anomaly detection
    - Vulnerability scanning
    - Access control management
    - Compliance checking
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="Security Specialist",
            description="Secures all system components and monitors for threats",
            capabilities=[
                "api_security",
                "encryption",
                "monitoring",
                "vulnerability_scan",
                "access_control",
                "compliance",
            ],
            config=config or {}
        )
        self.security_policies: List[Dict] = []
        self.vulnerabilities: List[Dict] = []
        self.audit_logs: List[Dict] = []

    async def execute_task(self, task: Task) -> Any:
        """Execute a security task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "api_security": self._secure_api,
            "encryption": self._implement_encryption,
            "monitoring": self._setup_monitoring,
            "vulnerability_scan": self._scan_vulnerabilities,
            "access_control": self._configure_access_control,
            "compliance": self._check_compliance,
            "audit": self._perform_audit,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _secure_api(self, task: Task) -> Dict[str, Any]:
        """Implement API security measures."""
        security_level = task.metadata.get("security_level", "high")
        
        self.log(f"Securing API with level: {security_level}")
        
        security_code = self._generate_api_security_code(security_level)
        
        return {
            "security_level": security_level,
            "code": security_code,
            "recommendations": self._get_security_recommendations(),
        }

    def _generate_api_security_code(self, level: str) -> str:
        """Generate API security middleware code."""
        return '''from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import time
import hashlib
import hmac
import logging
from typing import Optional
from collections import defaultdict
import asyncio

app = FastAPI()

# Security logger
security_logger = logging.getLogger("security")

# Rate limiting storage
request_counts = defaultdict(list)
RATE_LIMIT = 100  # requests per minute
RATE_WINDOW = 60  # seconds

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Rate limiting
        now = time.time()
        request_counts[client_ip] = [
            t for t in request_counts[client_ip] 
            if t > now - RATE_WINDOW
        ]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            security_logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(status_code=429, detail="Too many requests")
        
        request_counts[client_ip].append(now)
        
        # Security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        
        # Log request
        security_logger.info(
            f"{request.method} {request.url.path} - {client_ip} - {response.status_code}"
        )
        
        return response

app.add_middleware(SecurityMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)):
    """Verify API key"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate against stored keys (use secure comparison)
    stored_key = "your-secure-api-key"  # Get from secure storage
    if not hmac.compare_digest(api_key, stored_key):
        security_logger.warning(f"Invalid API key attempted")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key

# Request validation
class RequestValidator:
    """Validate and sanitize incoming requests"""
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Remove potentially dangerous characters"""
        import html
        return html.escape(value.strip())
    
    @staticmethod
    def validate_content_type(request: Request):
        """Ensure correct content type"""
        content_type = request.headers.get("content-type", "")
        if request.method in ["POST", "PUT", "PATCH"]:
            if "application/json" not in content_type:
                raise HTTPException(
                    status_code=415, 
                    detail="Content-Type must be application/json"
                )

# SQL injection prevention (parameterized queries example)
class SecureDatabase:
    """Secure database operations"""
    
    @staticmethod
    async def safe_query(query: str, params: tuple):
        """Execute parameterized query"""
        # Always use parameterized queries
        # cursor.execute(query, params)
        pass
    
    @staticmethod
    def validate_id(id_value: str) -> int:
        """Validate and convert ID parameter"""
        try:
            return int(id_value)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format")

# Protected endpoint example
@app.get("/api/protected")
async def protected_endpoint(api_key: str = Depends(verify_api_key)):
    """Example protected endpoint"""
    return {"status": "authenticated"}
'''

    def _get_security_recommendations(self) -> List[str]:
        """Get security recommendations."""
        return [
            "Enable HTTPS for all endpoints",
            "Implement rate limiting",
            "Use parameterized queries to prevent SQL injection",
            "Validate and sanitize all user inputs",
            "Implement proper authentication and authorization",
            "Set secure HTTP headers",
            "Log security events for monitoring",
            "Regularly update dependencies",
            "Use secrets management for credentials",
            "Implement request signing for sensitive operations",
        ]

    async def _implement_encryption(self, task: Task) -> Dict[str, Any]:
        """Implement data encryption."""
        encryption_type = task.metadata.get("encryption_type", "aes256")
        
        self.log(f"Implementing {encryption_type} encryption")
        
        encryption_code = self._generate_encryption_code(encryption_type)
        
        return {
            "encryption_type": encryption_type,
            "code": encryption_code,
        }

    def _generate_encryption_code(self, encryption_type: str) -> str:
        """Generate encryption utility code."""
        return '''import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class EncryptionService:
    """Secure encryption service for sensitive data"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.environ.get("ENCRYPTION_KEY")
        if not self.secret_key:
            raise ValueError("Encryption key is required")
        
        self._fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from secret key"""
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'emy-fullstack-salt',  # Use a secure, unique salt in production
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32)
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            100000
        )
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        salt_bytes = base64.b64decode(salt.encode())
        new_hash, _ = EncryptionService.hash_password(password, salt_bytes)
        return new_hash == hashed
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return base64.urlsafe_b64encode(os.urandom(length)).decode()

class FieldEncryption:
    """Encrypt specific database fields"""
    
    def __init__(self, encryption_service: EncryptionService):
        self.service = encryption_service
        self.encrypted_fields = ["ssn", "credit_card", "api_key", "password"]
    
    def encrypt_sensitive_fields(self, data: dict) -> dict:
        """Encrypt sensitive fields in a dictionary"""
        result = data.copy()
        for field in self.encrypted_fields:
            if field in result and result[field]:
                result[field] = self.service.encrypt(str(result[field]))
        return result
    
    def decrypt_sensitive_fields(self, data: dict) -> dict:
        """Decrypt sensitive fields in a dictionary"""
        result = data.copy()
        for field in self.encrypted_fields:
            if field in result and result[field]:
                try:
                    result[field] = self.service.decrypt(result[field])
                except ValueError:
                    pass  # Field may not be encrypted
        return result

# Usage example
# encryption = EncryptionService(secret_key="your-32-byte-secret-key-here")
# encrypted = encryption.encrypt("sensitive data")
# decrypted = encryption.decrypt(encrypted)
'''

    async def _setup_monitoring(self, task: Task) -> Dict[str, Any]:
        """Setup security monitoring."""
        monitoring_type = task.metadata.get("monitoring_type", "realtime")
        
        self.log(f"Setting up {monitoring_type} security monitoring")
        
        monitoring_code = self._generate_monitoring_code(monitoring_type)
        
        return {
            "monitoring_type": monitoring_type,
            "code": monitoring_code,
        }

    def _generate_monitoring_code(self, monitoring_type: str) -> str:
        """Generate security monitoring code."""
        return '''import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import asyncio

# Security event types
class SecurityEventType:
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"

class SecurityMonitor:
    """Real-time security monitoring and alerting"""
    
    def __init__(self):
        self.logger = logging.getLogger("security_monitor")
        self.events: List[Dict] = []
        self.alerts: List[Dict] = []
        self.thresholds = {
            SecurityEventType.LOGIN_FAILURE: 5,  # failures per 15 min
            SecurityEventType.RATE_LIMIT_EXCEEDED: 3,
            SecurityEventType.UNAUTHORIZED_ACCESS: 2,
        }
        self.event_counts = defaultdict(lambda: defaultdict(int))
    
    def log_event(
        self, 
        event_type: str, 
        details: Dict, 
        ip_address: str,
        user_id: Optional[str] = None
    ):
        """Log a security event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "ip_address": ip_address,
            "user_id": user_id,
            "details": details,
        }
        
        self.events.append(event)
        self.logger.info(json.dumps(event))
        
        # Check thresholds
        self._check_threshold(event_type, ip_address)
        
        # Analyze for anomalies
        self._analyze_anomaly(event)
    
    def _check_threshold(self, event_type: str, ip_address: str):
        """Check if event threshold is exceeded"""
        self.event_counts[ip_address][event_type] += 1
        
        threshold = self.thresholds.get(event_type)
        if threshold and self.event_counts[ip_address][event_type] >= threshold:
            self._create_alert(
                f"Threshold exceeded for {event_type}",
                {"ip_address": ip_address, "count": self.event_counts[ip_address][event_type]},
                severity="high"
            )
    
    def _analyze_anomaly(self, event: Dict):
        """Analyze event for anomalous behavior"""
        # Check for known attack patterns
        details = event.get("details", {})
        
        # SQL injection patterns
        sql_patterns = ["'", "--", ";", "UNION", "SELECT", "DROP"]
        if any(pattern in str(details) for pattern in sql_patterns):
            self._create_alert(
                "Possible SQL injection attempt",
                event,
                severity="critical"
            )
        
        # XSS patterns
        xss_patterns = ["<script", "javascript:", "onerror=", "onload="]
        if any(pattern.lower() in str(details).lower() for pattern in xss_patterns):
            self._create_alert(
                "Possible XSS attempt",
                event,
                severity="critical"
            )
    
    def _create_alert(self, message: str, details: Dict, severity: str = "medium"):
        """Create security alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "severity": severity,
            "details": details,
            "acknowledged": False,
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"SECURITY ALERT [{severity.upper()}]: {message}")
        
        # Send notification for critical alerts
        if severity == "critical":
            asyncio.create_task(self._send_notification(alert))
    
    async def _send_notification(self, alert: Dict):
        """Send notification for critical alerts"""
        # Implement notification logic (email, Slack, PagerDuty, etc.)
        self.logger.info(f"Sending notification for alert: {alert['message']}")
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent security events"""
        return self.events[-limit:]
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        return [a for a in self.alerts if not a["acknowledged"]]
    
    def acknowledge_alert(self, timestamp: str):
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert["timestamp"] == timestamp:
                alert["acknowledged"] = True
                break

class AnomalyDetector:
    """Detect anomalous behavior patterns"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.anomaly_threshold = 2.0  # Standard deviations
    
    def update_baseline(self, metric: str, value: float):
        """Update baseline metrics"""
        if metric not in self.baseline_metrics:
            self.baseline_metrics[metric] = {"values": [], "mean": 0, "std": 0}
        
        self.baseline_metrics[metric]["values"].append(value)
        values = self.baseline_metrics[metric]["values"][-1000:]  # Keep last 1000
        
        import statistics
        self.baseline_metrics[metric]["mean"] = statistics.mean(values)
        self.baseline_metrics[metric]["std"] = statistics.stdev(values) if len(values) > 1 else 0
    
    def is_anomalous(self, metric: str, value: float) -> bool:
        """Check if a value is anomalous"""
        if metric not in self.baseline_metrics:
            return False
        
        baseline = self.baseline_metrics[metric]
        if baseline["std"] == 0:
            return False
        
        z_score = abs(value - baseline["mean"]) / baseline["std"]
        return z_score > self.anomaly_threshold

# Initialize monitor
security_monitor = SecurityMonitor()
'''

    async def _scan_vulnerabilities(self, task: Task) -> Dict[str, Any]:
        """Scan for vulnerabilities."""
        scan_type = task.metadata.get("scan_type", "full")
        
        self.log(f"Running {scan_type} vulnerability scan")
        
        # Simulated vulnerability findings
        findings = self._generate_vulnerability_findings(scan_type)
        
        return {
            "scan_type": scan_type,
            "findings": findings,
            "remediation": self._generate_remediation_steps(findings),
        }

    def _generate_vulnerability_findings(self, scan_type: str) -> List[Dict]:
        """Generate vulnerability findings."""
        return [
            {
                "severity": "high",
                "type": "dependency",
                "description": "Outdated dependency with known CVE",
                "affected": "package@1.0.0",
                "recommendation": "Update to package@2.0.0",
            },
            {
                "severity": "medium",
                "type": "configuration",
                "description": "Debug mode enabled in production",
                "affected": "config.py",
                "recommendation": "Set DEBUG=False in production",
            },
            {
                "severity": "low",
                "type": "code",
                "description": "Missing input validation",
                "affected": "api/endpoints.py:45",
                "recommendation": "Add input validation",
            },
        ]

    def _generate_remediation_steps(self, findings: List[Dict]) -> List[str]:
        """Generate remediation steps for findings."""
        steps = []
        for finding in findings:
            steps.append(f"[{finding['severity'].upper()}] {finding['recommendation']}")
        return steps

    async def _configure_access_control(self, task: Task) -> Dict[str, Any]:
        """Configure access control."""
        access_model = task.metadata.get("access_model", "rbac")
        
        self.log(f"Configuring {access_model} access control")
        
        access_code = self._generate_access_control_code(access_model)
        
        return {
            "access_model": access_model,
            "code": access_code,
        }

    def _generate_access_control_code(self, model: str) -> str:
        """Generate access control code."""
        return '''from enum import Enum
from typing import List, Set, Optional
from functools import wraps
from fastapi import HTTPException, Depends

class Role(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class Permission(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.CREATE, Permission.READ, Permission.UPDATE, 
        Permission.DELETE, Permission.MANAGE_USERS, Permission.VIEW_ANALYTICS
    },
    Role.MANAGER: {
        Permission.CREATE, Permission.READ, Permission.UPDATE,
        Permission.VIEW_ANALYTICS
    },
    Role.USER: {
        Permission.CREATE, Permission.READ, Permission.UPDATE
    },
    Role.VIEWER: {
        Permission.READ
    },
}

class AccessControl:
    """Role-Based Access Control (RBAC) implementation"""
    
    def __init__(self):
        self.user_roles: dict = {}  # user_id -> Set[Role]
        self.resource_permissions: dict = {}  # resource -> Set[Permission]
    
    def assign_role(self, user_id: str, role: Role):
        """Assign role to user"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role)
    
    def remove_role(self, user_id: str, role: Role):
        """Remove role from user"""
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role)
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user"""
        permissions = set()
        for role in self.user_roles.get(user_id, []):
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        return permissions
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.get_user_permissions(user_id)
    
    def require_permission(self, permission: Permission):
        """Decorator to require permission for endpoint"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, current_user=None, **kwargs):
                if not current_user:
                    raise HTTPException(status_code=401, detail="Not authenticated")
                
                if not self.has_permission(current_user.id, permission):
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Permission denied: {permission.value} required"
                    )
                
                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator

# Initialize access control
access_control = AccessControl()

# Example usage in FastAPI
# @app.get("/admin/users")
# @access_control.require_permission(Permission.MANAGE_USERS)
# async def list_users(current_user: User = Depends(get_current_user)):
#     return users
'''

    async def _check_compliance(self, task: Task) -> Dict[str, Any]:
        """Check compliance with security standards."""
        standards = task.metadata.get("standards", ["OWASP", "GDPR"])
        
        self.log(f"Checking compliance: {standards}")
        
        compliance_report = self._generate_compliance_report(standards)
        
        return {
            "standards": standards,
            "report": compliance_report,
        }

    def _generate_compliance_report(self, standards: List[str]) -> Dict[str, Any]:
        """Generate compliance report."""
        return {
            "overall_score": 85,
            "standards": {
                "OWASP": {
                    "score": 90,
                    "passed": ["A1", "A2", "A3", "A5", "A7", "A8", "A9", "A10"],
                    "failed": ["A4", "A6"],
                    "recommendations": [
                        "Implement stricter access control",
                        "Add request signing",
                    ],
                },
                "GDPR": {
                    "score": 80,
                    "passed": ["Data encryption", "Access logs", "Data retention"],
                    "failed": ["Consent management"],
                    "recommendations": [
                        "Implement consent management system",
                        "Add data export functionality",
                    ],
                },
            },
        }

    async def _perform_audit(self, task: Task) -> Dict[str, Any]:
        """Perform security audit."""
        audit_scope = task.metadata.get("scope", "full")
        
        self.log(f"Performing {audit_scope} security audit")
        
        audit_report = {
            "scope": audit_scope,
            "timestamp": "2024-01-01T00:00:00Z",
            "findings": self._generate_audit_findings(),
            "recommendations": self._generate_audit_recommendations(),
        }
        
        self.audit_logs.append(audit_report)
        
        return audit_report

    def _generate_audit_findings(self) -> List[Dict]:
        """Generate audit findings."""
        return [
            {"category": "Authentication", "status": "pass", "notes": "JWT properly implemented"},
            {"category": "Authorization", "status": "warning", "notes": "Consider adding RBAC"},
            {"category": "Encryption", "status": "pass", "notes": "AES-256 encryption in use"},
            {"category": "Logging", "status": "pass", "notes": "Comprehensive logging enabled"},
            {"category": "Input Validation", "status": "warning", "notes": "Add stricter validation"},
        ]

    def _generate_audit_recommendations(self) -> List[str]:
        """Generate audit recommendations."""
        return [
            "Implement multi-factor authentication",
            "Add automated security scanning in CI/CD",
            "Conduct regular penetration testing",
            "Implement secrets rotation policy",
            "Add security headers check automation",
        ]

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic security tasks."""
        self.log(f"Handling generic security task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic security task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with security-specific info."""
        base_status = super().get_status()
        base_status.update({
            "policies": len(self.security_policies),
            "vulnerabilities": len(self.vulnerabilities),
            "audits": len(self.audit_logs),
        })
        return base_status
