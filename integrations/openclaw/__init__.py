# OpenClaw Integration
# Automation framework for posting, scraping, and external integrations
# Control Plane for the Emy-FullStack agent system

from .client import OpenClawClient, OpenClawConfig
from .scraper import WebScraper, ScrapingResult, ScrapingTask
from .poster import ContentPoster, PostResult, Platform
from .automation import AutomationEngine, AutomationTask, AutomationWorkflow
from .control_plane import (
    OpenClawControlPlane,
    CommandType,
    CommandRequest,
    CommandResponse,
    TaskPriority,
    app as control_plane_app,
    run_server as run_control_plane,
)

__all__ = [
    # Control Plane (Main entry point)
    'OpenClawControlPlane',
    'CommandType',
    'CommandRequest',
    'CommandResponse',
    'TaskPriority',
    'control_plane_app',
    'run_control_plane',
    # Client
    'OpenClawClient',
    'OpenClawConfig',
    # Scraper
    'WebScraper',
    'ScrapingResult',
    'ScrapingTask',
    # Poster
    'ContentPoster',
    'PostResult',
    'Platform',
    # Automation
    'AutomationEngine',
    'AutomationTask',
    'AutomationWorkflow',
]
