"""
Content Poster
Multi-platform content posting for OpenClaw integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import uuid


class Platform(Enum):
    """Supported posting platforms"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    MEDIUM = "medium"
    WORDPRESS = "wordpress"
    CUSTOM_API = "custom_api"


class PostStatus(Enum):
    """Post status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class MediaType(Enum):
    """Media types for posts"""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"
    DOCUMENT = "document"


@dataclass
class MediaAttachment:
    """Media attachment for a post"""
    media_type: MediaType
    url: Optional[str] = None
    file_path: Optional[str] = None
    alt_text: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None  # For videos
    dimensions: Optional[Dict[str, int]] = None  # width, height
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'media_type': self.media_type.value,
            'url': self.url,
            'file_path': self.file_path,
            'alt_text': self.alt_text,
            'thumbnail_url': self.thumbnail_url,
            'duration': self.duration,
            'dimensions': self.dimensions,
        }


@dataclass
class PostContent:
    """Content for a post"""
    text: str
    title: Optional[str] = None
    media: List[MediaAttachment] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    link: Optional[str] = None
    link_preview: bool = True
    location: Optional[Dict[str, Any]] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'title': self.title,
            'media': [m.to_dict() for m in self.media],
            'hashtags': self.hashtags,
            'mentions': self.mentions,
            'link': self.link,
            'link_preview': self.link_preview,
            'location': self.location,
            'custom_fields': self.custom_fields,
        }
    
    def get_full_text(self) -> str:
        """Get text with hashtags and mentions"""
        parts = [self.text]
        
        if self.mentions:
            parts.append(' '.join(f'@{m}' for m in self.mentions))
        
        if self.hashtags:
            parts.append(' '.join(f'#{h}' for h in self.hashtags))
        
        return ' '.join(parts)


@dataclass
class PostResult:
    """Result of a posting operation"""
    post_id: str
    platform: Platform
    status: PostStatus
    platform_post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'post_id': self.post_id,
            'platform': self.platform.value,
            'status': self.status.value,
            'platform_post_id': self.platform_post_id,
            'url': self.url,
            'error': self.error,
            'metrics': self.metrics,
            'created_at': self.created_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }


@dataclass
class PlatformConfig:
    """Configuration for a platform"""
    platform: Platform
    enabled: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    access_token_secret: Optional[str] = None
    account_id: Optional[str] = None
    custom_endpoint: Optional[str] = None
    max_text_length: int = 280
    max_media_count: int = 4
    supported_media_types: List[MediaType] = field(default_factory=list)
    rate_limit: int = 100  # posts per hour
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'platform': self.platform.value,
            'enabled': self.enabled,
            'account_id': self.account_id,
            'max_text_length': self.max_text_length,
            'max_media_count': self.max_media_count,
            'rate_limit': self.rate_limit,
        }


class ContentPoster:
    """
    Multi-platform content poster
    Handles scheduling, posting, and tracking across platforms
    """
    
    # Platform-specific text limits
    TEXT_LIMITS = {
        Platform.TWITTER: 280,
        Platform.FACEBOOK: 63206,
        Platform.INSTAGRAM: 2200,
        Platform.LINKEDIN: 3000,
        Platform.PINTEREST: 500,
        Platform.TIKTOK: 150,
        Platform.YOUTUBE: 5000,
        Platform.REDDIT: 40000,
        Platform.MEDIUM: 100000,
        Platform.WORDPRESS: 100000,
    }
    
    def __init__(self):
        self._platforms: Dict[Platform, PlatformConfig] = {}
        self._scheduled_posts: Dict[str, Dict[str, Any]] = {}
        self._post_history: List[PostResult] = []
        self._rate_limits: Dict[Platform, List[datetime]] = {}
        self._platform_handlers: Dict[Platform, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default posting handlers"""
        # These would be implemented for actual platforms
        for platform in Platform:
            self._platform_handlers[platform] = self._generic_post_handler
    
    def configure_platform(self, config: PlatformConfig):
        """Configure a platform"""
        self._platforms[config.platform] = config
        self._rate_limits[config.platform] = []
    
    def register_handler(self, platform: Platform, handler: Callable):
        """Register a custom posting handler for a platform"""
        self._platform_handlers[platform] = handler
    
    async def post(
        self,
        platform: Platform,
        content: PostContent,
        publish_immediately: bool = True,
    ) -> PostResult:
        """Post content to a platform"""
        post_id = str(uuid.uuid4())
        
        # Check platform configuration
        config = self._platforms.get(platform)
        if not config or not config.enabled:
            return PostResult(
                post_id=post_id,
                platform=platform,
                status=PostStatus.FAILED,
                error=f'Platform {platform.value} not configured or disabled',
            )
        
        # Validate content
        validation_error = self._validate_content(platform, content, config)
        if validation_error:
            return PostResult(
                post_id=post_id,
                platform=platform,
                status=PostStatus.FAILED,
                error=validation_error,
            )
        
        # Check rate limit
        if not self._check_rate_limit(platform, config):
            return PostResult(
                post_id=post_id,
                platform=platform,
                status=PostStatus.FAILED,
                error='Rate limit exceeded',
            )
        
        if not publish_immediately:
            return PostResult(
                post_id=post_id,
                platform=platform,
                status=PostStatus.DRAFT,
            )
        
        # Post using handler
        try:
            handler = self._platform_handlers.get(platform)
            if handler:
                result = await handler(platform, content, config, post_id)
                self._post_history.append(result)
                self._record_rate_limit(platform)
                return result
            else:
                return PostResult(
                    post_id=post_id,
                    platform=platform,
                    status=PostStatus.FAILED,
                    error='No handler for platform',
                )
        except Exception as e:
            return PostResult(
                post_id=post_id,
                platform=platform,
                status=PostStatus.FAILED,
                error=str(e),
            )
    
    async def post_to_multiple(
        self,
        platforms: List[Platform],
        content: PostContent,
        adapt_content: bool = True,
    ) -> Dict[Platform, PostResult]:
        """Post content to multiple platforms"""
        results = {}
        
        for platform in platforms:
            # Adapt content for platform if needed
            platform_content = content
            if adapt_content:
                platform_content = self._adapt_content(platform, content)
            
            results[platform] = await self.post(platform, platform_content)
        
        return results
    
    def schedule_post(
        self,
        platform: Platform,
        content: PostContent,
        publish_at: datetime,
    ) -> str:
        """Schedule a post for future publication"""
        post_id = str(uuid.uuid4())
        
        self._scheduled_posts[post_id] = {
            'post_id': post_id,
            'platform': platform,
            'content': content.to_dict(),
            'publish_at': publish_at,
            'status': PostStatus.SCHEDULED,
            'created_at': datetime.utcnow(),
        }
        
        return post_id
    
    def cancel_scheduled_post(self, post_id: str) -> bool:
        """Cancel a scheduled post"""
        if post_id in self._scheduled_posts:
            del self._scheduled_posts[post_id]
            return True
        return False
    
    def get_scheduled_posts(
        self,
        platform: Optional[Platform] = None,
    ) -> List[Dict[str, Any]]:
        """Get scheduled posts"""
        posts = list(self._scheduled_posts.values())
        
        if platform:
            posts = [p for p in posts if p['platform'] == platform]
        
        return sorted(posts, key=lambda p: p['publish_at'])
    
    async def process_scheduled_posts(self) -> List[PostResult]:
        """Process due scheduled posts"""
        now = datetime.utcnow()
        results = []
        
        for post_id, post_data in list(self._scheduled_posts.items()):
            if post_data['publish_at'] <= now:
                content = PostContent(**post_data['content'])
                result = await self.post(post_data['platform'], content)
                results.append(result)
                del self._scheduled_posts[post_id]
        
        return results
    
    def _validate_content(
        self,
        platform: Platform,
        content: PostContent,
        config: PlatformConfig,
    ) -> Optional[str]:
        """Validate content for a platform"""
        # Check text length
        text_length = len(content.get_full_text())
        max_length = config.max_text_length or self.TEXT_LIMITS.get(platform, 10000)
        
        if text_length > max_length:
            return f'Text too long: {text_length} > {max_length}'
        
        # Check media count
        if len(content.media) > config.max_media_count:
            return f'Too many media attachments: {len(content.media)} > {config.max_media_count}'
        
        # Check media types
        if config.supported_media_types:
            for media in content.media:
                if media.media_type not in config.supported_media_types:
                    return f'Unsupported media type: {media.media_type.value}'
        
        return None
    
    def _adapt_content(self, platform: Platform, content: PostContent) -> PostContent:
        """Adapt content for a specific platform"""
        adapted = PostContent(
            text=content.text,
            title=content.title,
            media=list(content.media),
            hashtags=list(content.hashtags),
            mentions=list(content.mentions),
            link=content.link,
            link_preview=content.link_preview,
            location=content.location,
            custom_fields=dict(content.custom_fields),
        )
        
        # Truncate text if needed
        max_length = self.TEXT_LIMITS.get(platform, 10000)
        full_text = adapted.get_full_text()
        
        if len(full_text) > max_length:
            # Calculate space needed for hashtags and mentions
            extras = ''
            if adapted.mentions:
                extras += ' ' + ' '.join(f'@{m}' for m in adapted.mentions)
            if adapted.hashtags:
                extras += ' ' + ' '.join(f'#{h}' for h in adapted.hashtags)
            
            # Truncate main text
            available = max_length - len(extras) - 3  # space for "..."
            if available > 0:
                adapted.text = adapted.text[:available] + '...'
        
        # Platform-specific adaptations
        if platform == Platform.TWITTER:
            # Limit hashtags for Twitter
            adapted.hashtags = adapted.hashtags[:5]
        
        elif platform == Platform.INSTAGRAM:
            # Instagram allows more hashtags
            pass
        
        elif platform == Platform.LINKEDIN:
            # More professional tone adjustments could go here
            pass
        
        return adapted
    
    def _check_rate_limit(self, platform: Platform, config: PlatformConfig) -> bool:
        """Check if rate limit allows posting"""
        if platform not in self._rate_limits:
            self._rate_limits[platform] = []
        
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self._rate_limits[platform] = [
            ts for ts in self._rate_limits[platform]
            if ts > hour_ago
        ]
        
        return len(self._rate_limits[platform]) < config.rate_limit
    
    def _record_rate_limit(self, platform: Platform):
        """Record a post for rate limiting"""
        if platform not in self._rate_limits:
            self._rate_limits[platform] = []
        self._rate_limits[platform].append(datetime.utcnow())
    
    async def _generic_post_handler(
        self,
        platform: Platform,
        content: PostContent,
        config: PlatformConfig,
        post_id: str,
    ) -> PostResult:
        """Generic posting handler (placeholder for actual implementation)"""
        # This would be replaced with actual platform API calls
        # For now, simulate successful posting
        
        await asyncio.sleep(0.5)  # Simulate API call
        
        return PostResult(
            post_id=post_id,
            platform=platform,
            status=PostStatus.PUBLISHED,
            platform_post_id=f'{platform.value}_{uuid.uuid4().hex[:8]}',
            url=f'https://{platform.value}.com/post/{post_id}',
            published_at=datetime.utcnow(),
        )
    
    def get_post_history(
        self,
        platform: Optional[Platform] = None,
        status: Optional[PostStatus] = None,
        limit: int = 100,
    ) -> List[PostResult]:
        """Get posting history"""
        history = list(self._post_history)
        
        if platform:
            history = [p for p in history if p.platform == platform]
        
        if status:
            history = [p for p in history if p.status == status]
        
        return sorted(history, key=lambda p: p.created_at, reverse=True)[:limit]
    
    def get_analytics(
        self,
        platform: Optional[Platform] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get posting analytics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        history = [
            p for p in self._post_history
            if p.created_at >= cutoff
        ]
        
        if platform:
            history = [p for p in history if p.platform == platform]
        
        return {
            'total_posts': len(history),
            'successful_posts': sum(1 for p in history if p.status == PostStatus.PUBLISHED),
            'failed_posts': sum(1 for p in history if p.status == PostStatus.FAILED),
            'platforms': {
                plat.value: sum(1 for p in history if p.platform == plat)
                for plat in Platform
            },
            'period_days': days,
        }
