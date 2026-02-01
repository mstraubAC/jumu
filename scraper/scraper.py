#!/usr/bin/env python3
"""
Jugend musiziert Tournament Scraper CLI.

Entry point for the scraper CLI. Delegates to the async scraper.

Usage:
    uv run scraper/scraper.py [--force] [--season-filter=...] [--region-filter=...]
    uv run scraper/scraper.py --list-seasons
    uv run scraper/scraper.py --list-regions
    uv run scraper/scraper.py --list-all
"""

# Standard library
import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from scraper.src.scraper_async import main

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
