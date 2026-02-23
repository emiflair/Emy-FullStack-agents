"""
OpenClaw Client
Main client for OpenClaw automation platform integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import aiohttp
import json
import os
import hashlib


class AuthMethod(Enum):
    """Authentication methods"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"


@dataclass
class OpenClawConfig:
    """Configuration for OpenClaw client"""
    base_url: str = field(default_factory=lambda: os.getenv('OPENCLAW_BASE_URL', 'https://api.openclaw.io/v1'))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv('OPENCLAW_API_KEY'))
    auth_method: AuthMethod = AuthMethod.API_KEY
    
    # OAuth2 settings
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    
    # Request settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    rate_limit: int = 100  # requests per minute
    rate_limit_window: int = 60  # seconds
    
    # Features
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    enable_logging: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'base_url': self.base_url,
            'auth_method': self.auth_method.value,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'rate_limit': self.rate_limit,
            'enable_caching': self.enable_caching,
            'enable_logging': self.enable_logging,
        }


@dataclass
class APIResponse:
    """Response from OpenClaw API"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'status_code': self.status_code,
            'data': self.data,
            'error': self.error,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
        }


class OpenClawClient:
    """
    Client for OpenClaw automation platform
    Handles authentication, requests, and response processing
    """
    
    def __init__(self, config: Optional[OpenClawConfig] = None):
        self.config = config or OpenClawConfig()
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        # Rate limiting state
        self._request_timestamps: List[datetime] = []
        
        # Cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Session
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Emy-FullStack-OpenClaw/1.0',
        }
        
        if self.config.auth_method == AuthMethod.API_KEY and self.config.api_key:
            headers['X-API-Key'] = self.config.api_key
        elif self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        
        return headers
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.config.rate_limit_window)
        
        # Clean old timestamps
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > window_start
        ]
        
        # Check limit
        if len(self._request_timestamps) >= self.config.rate_limit:
            oldest = min(self._request_timestamps)
            wait_time = (oldest + timedelta(seconds=self.config.rate_limit_window) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self._request_timestamps.append(now)
    
    def _get_cache_key(self, method: str, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key"""
        key_data = f"{method}:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check cache for stored response"""
        if not self.config.enable_caching:
            return None
        
        cached = self._cache.get(cache_key)
        if cached:
            if datetime.utcnow() < cached['expiry']:
                return cached['data']
            else:
                del self._cache[cache_key]
        return None
    
    def _store_cache(self, cache_key: str, data: Dict[str, Any]):
        """Store response in cache"""
        if self.config.enable_caching:
            self._cache[cache_key] = {
                'data': data,
                'expiry': datetime.utcnow() + timedelta(seconds=self.config.cache_ttl),
            }
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> APIResponse:
        """Make an API request"""
        # Check cache for GET requests
        cache_key = None
        if method.upper() == 'GET' and use_cache:
            cache_key = self._get_cache_key(method, endpoint, params)
            cached = self._check_cache(cache_key)
            if cached:
                return APIResponse(
                    success=True,
                    status_code=200,
                    data=cached,
                )
        
        # Rate limiting
        await self._check_rate_limit()
        
        # Build URL
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        # Retry loop
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                session = await self._get_session()
                headers = self._get_headers()
                
                async with session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else None
                    
                    api_response = APIResponse(
                        success=response.status < 400,
                        status_code=response.status,
                        data=response_data,
                        headers=dict(response.headers),
                        request_id=response.headers.get('X-Request-ID'),
                    )
                    
                    if not api_response.success:
                        api_response.error = response_data.get('error', 'Unknown error') if response_data else f'HTTP {response.status}'
                    
                    # Cache successful GET responses
                    if api_response.success and cache_key and response_data:
                        self._store_cache(cache_key, response_data)
                    
                    return api_response
                    
            except asyncio.TimeoutError:
                last_error = 'Request timeout'
            except aiohttp.ClientError as e:
                last_error = str(e)
            
            # Wait before retry
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return APIResponse(
            success=False,
            status_code=0,
            error=last_error or 'Max retries exceeded',
        )
    
    # ========== Authentication ==========
    
    async def authenticate_oauth2(self, authorization_code: str) -> APIResponse:
        """Exchange authorization code for access token"""
        return await self.request(
            'POST',
            '/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret,
                'redirect_uri': self.config.redirect_uri,
            },
        )
    
    async def refresh_token(self, refresh_token: str) -> APIResponse:
        """Refresh access token"""
        response = await self.request(
            'POST',
            '/oauth/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret,
            },
        )
        
        if response.success and response.data:
            self._access_token = response.data.get('access_token')
            expires_in = response.data.get('expires_in', 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        
        return response
    
    def set_access_token(self, token: str, expiry: Optional[datetime] = None):
        """Set access token directly"""
        self._access_token = token
        self._token_expiry = expiry
    
    # ========== Scraping API ==========
    
    async def create_scraping_task(
        self,
        url: str,
        selectors: Dict[str, str],
        options: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Create a new scraping task"""
        return await self.request(
            'POST',
            '/scraping/tasks',
            data={
                'url': url,
                'selectors': selectors,
                'options': options or {},
            },
        )
    
    async def get_scraping_result(self, task_id: str) -> APIResponse:
        """Get scraping task result"""
        return await self.request('GET', f'/scraping/tasks/{task_id}')
    
    async def scrape_url(
        self,
        url: str,
        selectors: Dict[str, str],
        wait_for_result: bool = True,
        timeout: int = 60,
    ) -> APIResponse:
        """Scrape a URL and optionally wait for result"""
        # Create task
        create_response = await self.create_scraping_task(url, selectors)
        
        if not create_response.success or not create_response.data:
            return create_response
        
        task_id = create_response.data.get('task_id')
        
        if not wait_for_result:
            return create_response
        
        # Poll for result
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            result = await self.get_scraping_result(task_id)
            
            if result.success and result.data:
                status = result.data.get('status')
                if status == 'completed':
                    return result
                elif status == 'failed':
                    return APIResponse(
                        success=False,
                        status_code=200,
                        error=result.data.get('error', 'Scraping failed'),
                    )
            
            await asyncio.sleep(2)
        
        return APIResponse(
            success=False,
            status_code=0,
            error='Scraping timeout',
        )
    
    # ========== Posting API ==========
    
    async def create_post(
        self,
        platform: str,
        content: Dict[str, Any],
        schedule: Optional[datetime] = None,
    ) -> APIResponse:
        """Create a post on a platform"""
        data = {
            'platform': platform,
            'content': content,
        }
        
        if schedule:
            data['schedule'] = schedule.isoformat()
        
        return await self.request('POST', '/posting/posts', data=data)
    
    async def get_post_status(self, post_id: str) -> APIResponse:
        """Get post status"""
        return await self.request('GET', f'/posting/posts/{post_id}')
    
    async def delete_post(self, post_id: str) -> APIResponse:
        """Delete a scheduled post"""
        return await self.request('DELETE', f'/posting/posts/{post_id}')
    
    async def list_posts(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> APIResponse:
        """List posts"""
        params = {'limit': limit}
        if platform:
            params['platform'] = platform
        if status:
            params['status'] = status
        
        return await self.request('GET', '/posting/posts', params=params)
    
    # ========== Automation API ==========
    
    async def create_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        triggers: Optional[List[Dict[str, Any]]] = None,
    ) -> APIResponse:
        """Create an automation workflow"""
        return await self.request(
            'POST',
            '/automation/workflows',
            data={
                'name': name,
                'steps': steps,
                'triggers': triggers or [],
            },
        )
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Execute a workflow"""
        return await self.request(
            'POST',
            f'/automation/workflows/{workflow_id}/execute',
            data={'input': input_data or {}},
        )
    
    async def get_workflow_execution(self, execution_id: str) -> APIResponse:
        """Get workflow execution status"""
        return await self.request('GET', f'/automation/executions/{execution_id}')
    
    # ========== External Integrations ==========
    
    async def connect_integration(
        self,
        integration_type: str,
        credentials: Dict[str, str],
    ) -> APIResponse:
        """Connect an external integration"""
        return await self.request(
            'POST',
            '/integrations/connect',
            data={
                'type': integration_type,
                'credentials': credentials,
            },
        )
    
    async def list_integrations(self) -> APIResponse:
        """List connected integrations"""
        return await self.request('GET', '/integrations')
    
    async def call_integration(
        self,
        integration_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Call an integration action"""
        return await self.request(
            'POST',
            f'/integrations/{integration_id}/actions/{action}',
            data=params or {},
        )
    
    # ========== Utilities ==========
    
    async def health_check(self) -> APIResponse:
        """Check API health"""
        return await self.request('GET', '/health', use_cache=False)
    
    async def get_usage(self) -> APIResponse:
        """Get API usage statistics"""
        return await self.request('GET', '/usage')
    
    def clear_cache(self):
        """Clear response cache"""
        self._cache.clear()


# Synchronous wrapper for non-async contexts
class SyncOpenClawClient:
    """Synchronous wrapper for OpenClawClient"""
    
    def __init__(self, config: Optional[OpenClawConfig] = None):
        self._async_client = OpenClawClient(config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def _run(self, coro):
        return self._get_loop().run_until_complete(coro)
    
    def close(self):
        self._run(self._async_client.close())
    
    def scrape_url(self, url: str, selectors: Dict[str, str], **kwargs) -> APIResponse:
        return self._run(self._async_client.scrape_url(url, selectors, **kwargs))
    
    def create_post(self, platform: str, content: Dict[str, Any], **kwargs) -> APIResponse:
        return self._run(self._async_client.create_post(platform, content, **kwargs))
    
    def execute_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> APIResponse:
        return self._run(self._async_client.execute_workflow(workflow_id, input_data))
    
    def health_check(self) -> APIResponse:
        return self._run(self._async_client.health_check())
