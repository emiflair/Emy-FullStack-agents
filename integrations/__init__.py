# Integrations Package
# External service integrations for Emy-FullStack

from .openclaw import (
    OpenClawClient,
    OpenClawConfig,
    WebScraper,
    ScrapingResult,
    ContentPoster,
    PostResult,
    Platform,
    AutomationEngine,
    AutomationWorkflow,
)

__all__ = [
    'OpenClawClient',
    'OpenClawConfig',
    'WebScraper',
    'ScrapingResult',
    'ContentPoster',
    'PostResult',
    'Platform',
    'AutomationEngine',
    'AutomationWorkflow',
]
