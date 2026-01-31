#!/usr/bin/env python3
"""
Web scraper for Jugend musiziert tournament participants.

Scrapes the Jugend musiziert API asynchronously to extract tournament data
(seasons, schedules, participants). Uses aiohttp for efficient parallel
HTTP requests and caches results in JSON format.

Usage:
    uv run scraper/scraper.py [--force] [--season-filter=...] [--region-filter=...]
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import aiohttp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JugendMusiziertScraper:
    """Asynchronous scraper for Jugend musiziert tournament data.
    
    Fetches data from the official API endpoints using parallel aiohttp requests.
    Handles pagination automatically and normalizes response structures.
    """
    
    # API endpoints
    API_BASE: str = "https://api.jugend-musiziert.org/api"
    SEASONS_ENDPOINT: str = f"{API_BASE}/seasons"
    TIMETABLE_ENDPOINT: str = f"{API_BASE}/timetable"
    
    # Request configuration
    TIMEOUT: int = 10  # seconds
    USER_AGENT: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize scraper with optional base URL reference.
        
        Args:
            base_url: Base URL for reference (optional, for fallback HTML parsing).
        """
        self.base_url: Optional[str] = base_url
        self.collected_data: Dict[str, Any] = {}
    
    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Optional[Dict[str, Any]]:
        """Make an async HTTP GET request and parse JSON.
        
        Args:
            session: aiohttp ClientSession for connection reuse.
            url: URL to fetch.
        
        Returns:
            Parsed JSON response or None on failure.
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)
            async with session.get(
                url,
                timeout=timeout,
                headers={'User-Agent': self.USER_AGENT}
            ) as response:
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    async def fetch_seasons(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch seasons data from API.
        
        Args:
            session: aiohttp ClientSession for connection reuse.
        
        Returns:
            Seasons data dictionary or None if request fails.
        """
        logger.info(f"Fetching seasons from {self.SEASONS_ENDPOINT}")
        data = await self._make_request(session, self.SEASONS_ENDPOINT)
        if data:
            logger.info(f"Successfully fetched seasons data")
        return data
    
    async def fetch_timetable(
        self,
        session: aiohttp.ClientSession,
        season_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch all timetable/schedule data from API (handles pagination).
        
        Args:
            session: aiohttp ClientSession for connection reuse.
            season_id: Optional season ID to filter by.
        
        Returns:
            Combined timetable data or None if request fails.
        """
        url: str = self.TIMETABLE_ENDPOINT
        if season_id:
            url = f"{url}?season={season_id}"
        
        logger.info(f"Fetching timetable from {url}")
        all_entries: list = []
        page_count: int = 0
        next_url: Optional[str] = url
        
        while next_url:
            page_count += 1
            logger.info(f"Fetching timetable page {page_count}: {next_url}")
            
            data = await self._make_request(session, next_url)
            if not data:
                logger.warning(f"Failed to fetch page {page_count}")
                break
            
            # Collect entries from this page
            members: list = data.get("hydra:member", [])
            all_entries.extend(members)
            logger.info(f"  Page {page_count}: Retrieved {len(members)} timetable entries")
            
            # Check for next page
            view: Dict[str, Any] = data.get("hydra:view", {})
            next_url = view.get("hydra:next")
            
            if next_url and next_url.startswith("/"):
                # Make absolute URL if relative
                next_url = f"https://api.jugend-musiziert.org{next_url}"
        
        logger.info(
            f"Successfully fetched {page_count} pages of timetable data "
            f"({len(all_entries)} total entries)"
        )
        
        # Return combined data with same structure as API
        result: Dict[str, Any] = {
            "@context": "/api/contexts/TimetableGroup",
            "@id": "/api/timetable",
            "@type": "hydra:Collection",
            "hydra:member": all_entries,
            "hydra:totalItems": len(all_entries),
        }
        
        return result
    
    async def scrape(self) -> Dict[str, Any]:
        """Scrape all tournament data concurrently.
        
        Fetches seasons and timetable data in parallel using async/await.
        
        Returns:
            Dictionary containing all scraped data with keys: seasons, timetable.
        """
        async with aiohttp.ClientSession() as session:
            # Fetch seasons and timetable in parallel
            seasons_task = self.fetch_seasons(session)
            timetable_task = self.fetch_timetable(session)
            
            seasons, timetable = await asyncio.gather(
                seasons_task,
                timetable_task,
                return_exceptions=False
            )
            
            data: Dict[str, Any] = {
                'seasons': seasons,
                'timetable': timetable,
            }
            
            return data
    
    def save_data(
        self,
        data: Dict[str, Any],
        output_file: str = 'jugend_musiziert_data.json'
    ) -> None:
        """Save scraped data to a JSON file.
        
        Args:
            data: Data to save.
            output_file: Output file path.
        """
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Data saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")


async def main() -> int:
    """Main scraper execution.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("=" * 60)
    print("Jugend musiziert Tournament Scraper (Async)")
    print("=" * 60)
    
    try:
        logger.info("Starting scraper...")
        
        # Initialize scraper
        scraper = JugendMusiziertScraper()
        
        # Scrape all data in parallel
        logger.info("Fetching seasons and timetable concurrently...")
        all_data = await scraper.scrape()
        
        # Add metadata
        import datetime
        all_data['metadata'] = {
            'timestamp': datetime.datetime.now().isoformat(),
            'api_base': JugendMusiziertScraper.API_BASE,
        }
        
        # Save to file
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        output_file = data_dir / 'jugend_musiziert_data.json'
        scraper.save_data(all_data, str(output_file))
        
        # Print summary
        print("\n" + "=" * 60)
        print("SCRAPING SUMMARY")
        print("=" * 60)
        
        seasons_data = all_data.get('seasons')
        timetable_data = all_data.get('timetable')
        
        if seasons_data:
            season_count = len(seasons_data.get('hydra:member', []))
            print(f"✓ Seasons: {season_count} found")
        else:
            print("✗ Seasons: Failed to fetch")
        
        if timetable_data:
            entry_count = len(timetable_data.get('hydra:member', []))
            print(f"✓ Timetable: {entry_count} entries found")
        else:
            print("✗ Timetable: Failed to fetch")
        
        print(f"✓ Data saved to: {output_file}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
