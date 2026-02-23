"""
Backend Developer Agent
Responsible for implementing FastAPI/Flask endpoints, orchestrating Worker Agents,
and handling Master Brain workflow instructions.
"""

from typing import Any, Dict, List
from .base_agent import BaseAgent, Task


class BackendAgent(BaseAgent):
    """
    Backend Developer Agent for the Emy-FullStack system.
    
    Capabilities:
    - Implement FastAPI / Flask endpoints
    - Orchestrate Worker Agents (OpenClaw scripts, automation)
    - Handle Master Brain workflow instructions
    - Create API documentation
    - Setup middleware and authentication
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="Backend Developer",
            description="Builds backend APIs and orchestrates worker agents",
            capabilities=[
                "api_endpoint",
                "worker_orchestration",
                "authentication",
                "middleware",
                "database_integration",
                "api_documentation",
            ],
            config=config or {}
        )
        self.api_framework = config.get("api_framework", "fastapi") if config else "fastapi"
        self.generated_endpoints: List[str] = []
        self.generated_models: List[str] = []

    async def execute_task(self, task: Task) -> Any:
        """Execute a backend development task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "api_endpoint": self._create_endpoint,
            "worker_orchestration": self._orchestrate_workers,
            "authentication": self._setup_authentication,
            "middleware": self._create_middleware,
            "database_integration": self._integrate_database,
            "api_documentation": self._generate_api_docs,
            "crud_api": self._create_crud_api,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _create_endpoint(self, task: Task) -> Dict[str, Any]:
        """Create a new API endpoint."""
        endpoint_path = task.metadata.get("path", "/api/endpoint")
        method = task.metadata.get("method", "GET")
        endpoint_name = task.metadata.get("name", "endpoint")
        request_model = task.metadata.get("request_model")
        response_model = task.metadata.get("response_model")
        
        self.log(f"Creating endpoint: {method} {endpoint_path}")
        
        code = self._generate_endpoint_code(endpoint_path, method, endpoint_name, request_model, response_model)
        
        self.generated_endpoints.append(endpoint_path)
        
        return {
            "endpoint": endpoint_path,
            "method": method,
            "code": code,
        }

    def _generate_endpoint_code(
        self, 
        path: str, 
        method: str, 
        name: str,
        request_model: str = None,
        response_model: str = None
    ) -> str:
        """Generate FastAPI endpoint code."""
        response_model_annotation = f", response_model={response_model}" if response_model else ""
        request_param = f"data: {request_model}" if request_model else ""
        
        return f'''from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

# Request/Response Models
class {name.title()}Request(BaseModel):
    # Add request fields here
    pass

class {name.title()}Response(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

@router.{method.lower()}("{path}"{response_model_annotation})
async def {name}({request_param}):
    """
    {name.title()} endpoint
    
    Description: Handle {name} requests
    """
    try:
        # TODO: Implement business logic
        result = {{"message": "{name} processed successfully"}}
        return {name.title()}Response(
            success=True,
            message="Operation completed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

    async def _create_crud_api(self, task: Task) -> Dict[str, Any]:
        """Create a full CRUD API for a resource."""
        resource_name = task.metadata.get("resource_name", "item")
        fields = task.metadata.get("fields", [])
        
        self.log(f"Creating CRUD API for: {resource_name}")
        
        code = self._generate_crud_code(resource_name, fields)
        
        return {
            "resource": resource_name,
            "endpoints": [
                f"GET /api/{resource_name}s",
                f"GET /api/{resource_name}s/{{id}}",
                f"POST /api/{resource_name}s",
                f"PUT /api/{resource_name}s/{{id}}",
                f"DELETE /api/{resource_name}s/{{id}}",
            ],
            "code": code,
        }

    def _generate_crud_code(self, resource_name: str, fields: List[Dict]) -> str:
        """Generate full CRUD API code."""
        class_name = resource_name.title()
        field_definitions = "\n    ".join([
            f"{f.get('name', 'field')}: {f.get('type', 'str')}"
            for f in fields
        ]) if fields else "name: str\n    description: Optional[str] = None"
        
        return f'''from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/{resource_name}s", tags=["{resource_name}s"])

# Models
class {class_name}Base(BaseModel):
    {field_definitions}

class {class_name}Create({class_name}Base):
    pass

class {class_name}Update(BaseModel):
    {field_definitions}

class {class_name}(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    {field_definitions}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# In-memory storage (replace with database)
{resource_name}s_db: dict = {{}}

@router.get("/", response_model=List[{class_name}])
async def list_{resource_name}s(skip: int = 0, limit: int = 100):
    """List all {resource_name}s with pagination."""
    items = list({resource_name}s_db.values())
    return items[skip:skip + limit]

@router.get("/{{item_id}}", response_model={class_name})
async def get_{resource_name}(item_id: str):
    """Get a specific {resource_name} by ID."""
    if item_id not in {resource_name}s_db:
        raise HTTPException(status_code=404, detail="{class_name} not found")
    return {resource_name}s_db[item_id]

@router.post("/", response_model={class_name}, status_code=201)
async def create_{resource_name}(data: {class_name}Create):
    """Create a new {resource_name}."""
    item = {class_name}(**data.dict())
    {resource_name}s_db[item.id] = item
    return item

@router.put("/{{item_id}}", response_model={class_name})
async def update_{resource_name}(item_id: str, data: {class_name}Update):
    """Update an existing {resource_name}."""
    if item_id not in {resource_name}s_db:
        raise HTTPException(status_code=404, detail="{class_name} not found")
    
    existing = {resource_name}s_db[item_id]
    updated_data = data.dict(exclude_unset=True)
    updated_data["updated_at"] = datetime.now()
    
    for key, value in updated_data.items():
        setattr(existing, key, value)
    
    {resource_name}s_db[item_id] = existing
    return existing

@router.delete("/{{item_id}}", status_code=204)
async def delete_{resource_name}(item_id: str):
    """Delete a {resource_name}."""
    if item_id not in {resource_name}s_db:
        raise HTTPException(status_code=404, detail="{class_name} not found")
    del {resource_name}s_db[item_id]
    return None
'''

    async def _orchestrate_workers(self, task: Task) -> Dict[str, Any]:
        """Orchestrate worker agents for automation tasks."""
        worker_tasks = task.metadata.get("worker_tasks", [])
        parallel = task.metadata.get("parallel", False)
        
        self.log(f"Orchestrating {len(worker_tasks)} worker tasks")
        
        orchestration_code = self._generate_orchestration_code(worker_tasks, parallel)
        
        return {
            "worker_tasks": worker_tasks,
            "parallel": parallel,
            "orchestration_code": orchestration_code,
        }

    def _generate_orchestration_code(self, worker_tasks: List[Dict], parallel: bool) -> str:
        """Generate worker orchestration code."""
        return '''from celery import Celery, group, chain
from typing import List, Dict, Any
import asyncio

app = Celery('worker_orchestrator', broker='redis://localhost:6379/0')

@app.task
def execute_worker_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single worker task."""
    task_type = task_data.get("type")
    
    # Route to appropriate worker
    if task_type == "openclaw":
        return execute_openclaw_task(task_data)
    elif task_type == "automation":
        return execute_automation_task(task_data)
    else:
        return {"status": "completed", "result": task_data}

def execute_openclaw_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute OpenClaw automation task."""
    # TODO: Implement OpenClaw integration
    return {"status": "completed", "type": "openclaw"}

def execute_automation_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute general automation task."""
    # TODO: Implement automation logic
    return {"status": "completed", "type": "automation"}

async def orchestrate_tasks(tasks: List[Dict], parallel: bool = False):
    """Orchestrate multiple worker tasks."""
    if parallel:
        # Execute tasks in parallel
        job = group([execute_worker_task.s(task) for task in tasks])
        result = job.apply_async()
        return result.get()
    else:
        # Execute tasks sequentially
        results = []
        for task in tasks:
            result = execute_worker_task.delay(task)
            results.append(result.get())
        return results
'''

    async def _setup_authentication(self, task: Task) -> Dict[str, Any]:
        """Setup authentication system."""
        auth_type = task.metadata.get("auth_type", "jwt")
        
        self.log(f"Setting up {auth_type} authentication")
        
        auth_code = self._generate_auth_code(auth_type)
        
        return {
            "auth_type": auth_type,
            "code": auth_code,
        }

    def _generate_auth_code(self, auth_type: str) -> str:
        """Generate authentication code."""
        return '''from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    # TODO: Fetch user from database
    return User(username=token_data.username)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
'''

    async def _create_middleware(self, task: Task) -> Dict[str, Any]:
        """Create middleware components."""
        middleware_types = task.metadata.get("types", ["cors", "logging"])
        
        self.log(f"Creating middleware: {middleware_types}")
        
        middleware_code = self._generate_middleware_code(middleware_types)
        
        return {
            "types": middleware_types,
            "code": middleware_code,
        }

    def _generate_middleware_code(self, middleware_types: List[str]) -> str:
        """Generate middleware code."""
        code = '''from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

app = FastAPI()

'''
        if "cors" in middleware_types:
            code += '''# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
        if "logging" in middleware_types:
            code += '''# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logging.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )
    return response

'''
        return code

    async def _integrate_database(self, task: Task) -> Dict[str, Any]:
        """Create database integration code."""
        db_type = task.metadata.get("db_type", "postgresql")
        orm = task.metadata.get("orm", "sqlalchemy")
        
        self.log(f"Integrating {db_type} with {orm}")
        
        db_code = self._generate_db_integration(db_type, orm)
        
        return {
            "db_type": db_type,
            "orm": orm,
            "code": db_code,
        }

    def _generate_db_integration(self, db_type: str, orm: str) -> str:
        """Generate database integration code."""
        return '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Database URL
DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator:
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in endpoints:
# from fastapi import Depends
# from .database import get_db
# from sqlalchemy.orm import Session
#
# @router.get("/items")
# def get_items(db: Session = Depends(get_db)):
#     return db.query(Item).all()
'''

    async def _generate_api_docs(self, task: Task) -> Dict[str, Any]:
        """Generate API documentation."""
        title = task.metadata.get("title", "API Documentation")
        version = task.metadata.get("version", "1.0.0")
        
        self.log(f"Generating API documentation: {title}")
        
        return {
            "title": title,
            "version": version,
            "code": self._generate_docs_config(title, version),
        }

    def _generate_docs_config(self, title: str, version: str) -> str:
        """Generate OpenAPI documentation configuration."""
        return f'''from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="{title}",
    version="{version}",
    description="Auto-generated API documentation",
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="{title}",
        version="{version}",
        description="API documentation for the Emy-FullStack system",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {{
        "url": "https://example.com/logo.png"
    }}
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
'''

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic backend tasks."""
        self.log(f"Handling generic backend task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic backend task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with backend-specific info."""
        base_status = super().get_status()
        base_status.update({
            "api_framework": self.api_framework,
            "generated_endpoints": self.generated_endpoints,
            "generated_models": self.generated_models,
        })
        return base_status
