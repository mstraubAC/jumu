"""Scraper source modules.

This package contains the core scraping logic:
- scraper: Main synchronous scraper
- scraper_async: Async scraper with aiohttp
- version_manager: Smart versioning system
"""

from scraper.src.scraper import JugendMusiziertScraper
from scraper.src.version_manager import VersionManager

__all__ = ["JugendMusiziertScraper", "VersionManager"]
