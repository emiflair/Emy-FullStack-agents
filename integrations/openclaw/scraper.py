"""
Web Scraper
Advanced web scraping capabilities for OpenClaw integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from enum import Enum
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
import hashlib


class ScrapingMethod(Enum):
    """Scraping methods"""
    CSS_SELECTOR = "css"
    XPATH = "xpath"
    REGEX = "regex"
    JSON_PATH = "jsonpath"


class ContentType(Enum):
    """Content types for extraction"""
    TEXT = "text"
    HTML = "html"
    ATTRIBUTE = "attribute"
    ALL_TEXT = "all_text"
    TABLE = "table"
    LIST = "list"


@dataclass
class Selector:
    """Selector configuration for scraping"""
    name: str
    selector: str
    method: ScrapingMethod = ScrapingMethod.CSS_SELECTOR
    content_type: ContentType = ContentType.TEXT
    attribute: Optional[str] = None  # For ATTRIBUTE content type
    multiple: bool = False  # Extract all matches vs first
    transform: Optional[Callable[[str], str]] = None
    default: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'selector': self.selector,
            'method': self.method.value,
            'content_type': self.content_type.value,
            'attribute': self.attribute,
            'multiple': self.multiple,
            'default': self.default,
        }


@dataclass
class ScrapingTask:
    """A scraping task configuration"""
    task_id: str
    url: str
    selectors: List[Selector]
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    delay: float = 0  # Delay before scraping
    follow_redirects: bool = True
    javascript_render: bool = False
    proxy: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'url': self.url,
            'selectors': [s.to_dict() for s in self.selectors],
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'javascript_render': self.javascript_render,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    task_id: str
    url: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    raw_html: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'url': self.url,
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'extracted_at': self.extracted_at.isoformat(),
            'metadata': self.metadata,
        }


class WebScraper:
    """
    Advanced web scraper for extracting data from websites
    Supports CSS selectors, XPath, regex patterns
    """
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._task_counter = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session
    
    async def close(self):
        """Close the scraper session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _generate_task_id(self, url: str) -> str:
        """Generate unique task ID"""
        self._task_counter += 1
        return f"scrape_{hashlib.md5(url.encode()).hexdigest()[:8]}_{self._task_counter}"
    
    async def scrape(
        self,
        url: str,
        selectors: List[Selector],
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_count: int = 3,
        save_html: bool = False,
    ) -> ScrapingResult:
        """Scrape a URL with given selectors"""
        task_id = self._generate_task_id(url)
        
        # Merge headers
        request_headers = dict(self.DEFAULT_HEADERS)
        if headers:
            request_headers.update(headers)
        
        # Fetch page
        html = None
        status_code = None
        response_time = None
        
        for attempt in range(retry_count):
            try:
                session = await self._get_session()
                start_time = datetime.utcnow()
                
                async with session.get(
                    url,
                    headers=request_headers,
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                ) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds()
                    status_code = response.status
                    
                    if response.status == 200:
                        html = await response.text()
                        break
                    elif response.status >= 400:
                        return ScrapingResult(
                            task_id=task_id,
                            url=url,
                            success=False,
                            error=f'HTTP {response.status}',
                            status_code=status_code,
                            response_time=response_time,
                        )
                        
            except asyncio.TimeoutError:
                if attempt == retry_count - 1:
                    return ScrapingResult(
                        task_id=task_id,
                        url=url,
                        success=False,
                        error='Request timeout',
                    )
            except aiohttp.ClientError as e:
                if attempt == retry_count - 1:
                    return ScrapingResult(
                        task_id=task_id,
                        url=url,
                        success=False,
                        error=str(e),
                    )
            
            await asyncio.sleep(1 * (attempt + 1))
        
        if not html:
            return ScrapingResult(
                task_id=task_id,
                url=url,
                success=False,
                error='Failed to fetch page content',
            )
        
        # Parse and extract data
        try:
            extracted_data = self._extract_data(html, selectors)
            
            return ScrapingResult(
                task_id=task_id,
                url=url,
                success=True,
                data=extracted_data,
                raw_html=html if save_html else None,
                status_code=status_code,
                response_time=response_time,
                metadata={
                    'selector_count': len(selectors),
                    'html_length': len(html),
                },
            )
            
        except Exception as e:
            return ScrapingResult(
                task_id=task_id,
                url=url,
                success=False,
                error=f'Extraction error: {str(e)}',
                status_code=status_code,
                response_time=response_time,
            )
    
    def _extract_data(
        self,
        html: str,
        selectors: List[Selector],
    ) -> Dict[str, Any]:
        """Extract data from HTML using selectors"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        for selector in selectors:
            try:
                if selector.method == ScrapingMethod.CSS_SELECTOR:
                    value = self._extract_css(soup, selector)
                elif selector.method == ScrapingMethod.REGEX:
                    value = self._extract_regex(html, selector)
                elif selector.method == ScrapingMethod.XPATH:
                    value = self._extract_xpath(html, selector)
                else:
                    value = selector.default
                
                # Apply transform if provided
                if value and selector.transform:
                    if isinstance(value, list):
                        value = [selector.transform(v) for v in value]
                    else:
                        value = selector.transform(value)
                
                data[selector.name] = value if value else selector.default
                
            except Exception as e:
                data[selector.name] = selector.default
                data[f'{selector.name}_error'] = str(e)
        
        return data
    
    def _extract_css(self, soup: BeautifulSoup, selector: Selector) -> Any:
        """Extract using CSS selector"""
        if selector.multiple:
            elements = soup.select(selector.selector)
        else:
            element = soup.select_one(selector.selector)
            elements = [element] if element else []
        
        if not elements:
            return None
        
        results = []
        for element in elements:
            if selector.content_type == ContentType.TEXT:
                results.append(element.get_text(strip=True))
            elif selector.content_type == ContentType.HTML:
                results.append(str(element))
            elif selector.content_type == ContentType.ATTRIBUTE:
                results.append(element.get(selector.attribute, ''))
            elif selector.content_type == ContentType.ALL_TEXT:
                results.append(' '.join(element.stripped_strings))
            elif selector.content_type == ContentType.TABLE:
                results.append(self._extract_table(element))
            elif selector.content_type == ContentType.LIST:
                results.append([li.get_text(strip=True) for li in element.find_all('li')])
        
        return results if selector.multiple else results[0]
    
    def _extract_regex(self, html: str, selector: Selector) -> Any:
        """Extract using regex pattern"""
        pattern = re.compile(selector.selector, re.IGNORECASE | re.DOTALL)
        
        if selector.multiple:
            matches = pattern.findall(html)
            return matches if matches else None
        else:
            match = pattern.search(html)
            return match.group(1) if match and match.groups() else (match.group(0) if match else None)
    
    def _extract_xpath(self, html: str, selector: Selector) -> Any:
        """Extract using XPath (requires lxml)"""
        try:
            from lxml import etree
            tree = etree.HTML(html)
            
            if selector.multiple:
                elements = tree.xpath(selector.selector)
            else:
                elements = tree.xpath(selector.selector)[:1]
            
            if not elements:
                return None
            
            results = []
            for element in elements:
                if isinstance(element, str):
                    results.append(element)
                else:
                    if selector.content_type == ContentType.TEXT:
                        results.append(element.text or '')
                    elif selector.content_type == ContentType.HTML:
                        results.append(etree.tostring(element, encoding='unicode'))
                    elif selector.content_type == ContentType.ATTRIBUTE:
                        results.append(element.get(selector.attribute, ''))
                    else:
                        results.append(element.text or '')
            
            return results if selector.multiple else results[0]
            
        except ImportError:
            raise ValueError("lxml is required for XPath extraction")
    
    def _extract_table(self, element) -> List[Dict[str, str]]:
        """Extract table data as list of dicts"""
        rows = element.find_all('tr')
        if not rows:
            return []
        
        # Get headers
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Get data rows
        data = []
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) == len(headers):
                data.append({
                    headers[i]: cells[i].get_text(strip=True)
                    for i in range(len(headers))
                })
        
        return data
    
    async def scrape_multiple(
        self,
        urls: List[str],
        selectors: List[Selector],
        concurrency: int = 5,
        delay: float = 0.5,
    ) -> List[ScrapingResult]:
        """Scrape multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(url: str) -> ScrapingResult:
            async with semaphore:
                result = await self.scrape(url, selectors)
                if delay > 0:
                    await asyncio.sleep(delay)
                return result
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    def create_task(
        self,
        url: str,
        selectors: List[Selector],
        **kwargs,
    ) -> ScrapingTask:
        """Create a scraping task configuration"""
        return ScrapingTask(
            task_id=self._generate_task_id(url),
            url=url,
            selectors=selectors,
            **kwargs,
        )
    
    async def execute_task(self, task: ScrapingTask) -> ScrapingResult:
        """Execute a scraping task"""
        if task.delay > 0:
            await asyncio.sleep(task.delay)
        
        return await self.scrape(
            url=task.url,
            selectors=task.selectors,
            headers=task.headers,
            cookies=task.cookies,
            timeout=task.timeout,
            retry_count=task.retry_count,
        )


# Helper functions for common scraping patterns
def create_text_selector(name: str, css: str, multiple: bool = False) -> Selector:
    """Create a simple text selector"""
    return Selector(name=name, selector=css, content_type=ContentType.TEXT, multiple=multiple)


def create_link_selector(name: str, css: str, multiple: bool = False) -> Selector:
    """Create a link (href) selector"""
    return Selector(
        name=name,
        selector=css,
        content_type=ContentType.ATTRIBUTE,
        attribute='href',
        multiple=multiple,
    )


def create_image_selector(name: str, css: str, multiple: bool = False) -> Selector:
    """Create an image (src) selector"""
    return Selector(
        name=name,
        selector=css,
        content_type=ContentType.ATTRIBUTE,
        attribute='src',
        multiple=multiple,
    )


def create_table_selector(name: str, css: str) -> Selector:
    """Create a table selector"""
    return Selector(name=name, selector=css, content_type=ContentType.TABLE)
