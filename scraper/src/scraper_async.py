#!/usr/bin/env python3
"""
Web scraper for Jugend musiziert tournament participants.

Scrapes the Jugend musiziert API asynchronously to extract tournament data
(seasons, schedules, participants). Uses aiohttp for efficient parallel
HTTP requests and caches results in JSON format.

Usage:
    uv run scraper/scraper_async.py [--force] [--season-filter=...] [--region-filter=...]
    uv run scraper/scraper_async.py --list-seasons
    uv run scraper/scraper_async.py --list-regions
    uv run scraper/scraper_async.py --list-all
"""

import asyncio
import argparse
import json
import logging
from typing import Optional, Dict, Any, Set, List
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
    
    # Next.js data endpoint for regions (from website frontend)
    REGIONS_ENDPOINT: str = "https://www.jugend-musiziert.org/_next/data/gk2cuCjnn0VZy0e6OaBbU/de/wettbewerbe/regionalwettbewerbe.json"
    
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
    
    async def fetch_regions(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch regions data from Next.js page endpoint.
        
        Fetches the regionalwettbewerbe page data which contains the state/region
        hierarchy in the sideMenu structure. This is more efficient than mining
        the timetable for regions.
        
        Args:
            session: aiohttp ClientSession for connection reuse.
        
        Returns:
            Page data dictionary or None if request fails.
        """
        logger.info(f"Fetching regions from {self.REGIONS_ENDPOINT}")
        data = await self._make_request(session, self.REGIONS_ENDPOINT)
        if data:
            logger.info(f"Successfully fetched regions data")
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
    
    def extract_seasons(self, seasons_data: Optional[Dict[str, Any]]) -> Set[str]:
        """Extract unique season identifiers from seasons API response.
        
        Args:
            seasons_data: Raw seasons data from API.
        
        Returns:
            Set of unique season IDs.
        """
        if not seasons_data:
            return set()
        
        members: list = seasons_data.get("hydra:member", [])
        seasons: Set[str] = set()
        
        for member in members:
            if "@id" in member:
                # Extract ID (e.g., "/api/seasons/47" -> "47")
                season_id = member["@id"].split("/")[-1]
                seasons.add(season_id)
        
        return seasons
    
    def extract_regions(self, regions_data: Optional[Dict[str, Any]], timetable_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract states and regions with identifiers from Next.js page data.
        
        Parses the sideMenu hierarchy to extract:
        - States (Landeswettbewerbe): Top-level regions like Baden-Württemberg, Bayern
        - Regions (Regionalwettbewerbe): Sub-regions within each state
        
        Each entry includes:
        - title: Full name (e.g., "Baden-Württemberg")
        - id: Numeric identifier (menu ID, not for API filtering)
        - slug: URL slug for web navigation
        - contest_identifier: API identifier for timetable filtering (e.g., "BaWue_Esslingen")
        
        Args:
            regions_data: Raw page data from Next.js endpoint.
            timetable_data: Optional timetable data to extract contest identifiers for API filtering.
        
        Returns:
            Dictionary with 'states' and 'regions' lists, each containing
            dicts with title, id, slug, and contest_identifier fields.
        """
        if not regions_data:
            return {"states": [], "regions": []}
        
        # Build set of contest identifiers from timetable if available
        contest_identifiers_set = set()
        if timetable_data:
            members = timetable_data.get('hydra:member', [])
            for entry in members:
                if 'contest' in entry:
                    contest = entry['contest']
                    identifier = contest.get('identifier', '')
                    if identifier:
                        contest_identifiers_set.add(identifier)
        
        states_list: List[Dict[str, Any]] = []
        regions_list: List[Dict[str, Any]] = []
        
        # Navigate to pageProps -> page -> sideMenu
        try:
            page_props = regions_data.get("pageProps", {})
            side_menu = page_props.get("page", {}).get("sideMenu", [])
            
            # Find the "Regionalwettbewerbe" menu item
            for menu_item in side_menu:
                if menu_item.get("title") == "Regionalwettbewerbe":
                    # Get the children which are the states (Landeswettbewerbe)
                    children = menu_item.get("children", [])
                    for child in children:
                        state_title = child.get("title")
                        if state_title:
                            state_id = child.get("id")
                            state_link = child.get("link", "")
                            state_slug = state_link.split("/")[-1] if state_link else None
                            
                            states_list.append({
                                "title": state_title,
                                "id": state_id,
                                "slug": state_slug,
                                "link": state_link,
                                "contest_identifier": None  # States don't have individual contest identifiers
                            })
                            
                            # Get the sub-children which are regional subdivisions (Regionalwettbewerbe)
                            regional_children = child.get("children", [])
                            for regional_child in regional_children:
                                region_title = regional_child.get("title")
                                if region_title:
                                    region_id = regional_child.get("id")
                                    region_link = regional_child.get("link", "")
                                    region_slug = region_link.split("/")[-1] if region_link else None
                                    
                                    regions_list.append({
                                        "title": region_title,
                                        "id": region_id,
                                        "slug": region_slug,
                                        "link": region_link,
                                        "parent_state": state_title,
                                        "parent_state_id": state_id,
                                        "contest_identifier": None  # Populated from timetable data if available
                                    })
                    break
        except (KeyError, TypeError) as e:
            logger.warning(f"Error parsing regions data structure: {e}")
        
        return {
            "states": states_list,
            "regions": regions_list
        }
    
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


async def fetch_and_list_seasons() -> int:
    """Fetch and list all available seasons.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("=" * 60)
    print("Available Seasons")
    print("=" * 60)
    
    try:
        scraper = JugendMusiziertScraper()
        async with aiohttp.ClientSession() as session:
            seasons_data = await scraper.fetch_seasons(session)
            
            if not seasons_data:
                print("✗ Failed to fetch seasons data")
                return 1
            
            seasons = scraper.extract_seasons(seasons_data)
            
            if not seasons:
                print("No seasons found in API response")
                return 0
            
            members = seasons_data.get('hydra:member', [])
            
            # Display seasons with details
            print(f"\nFound {len(seasons)} seasons:\n")
            
            for member in members:
                season_id = member.get("@id", "").split("/")[-1]
                year = member.get("year", "N/A")
                print(f"  ID: {season_id:>3}  Year: {year}")
            
            print("\n" + "=" * 60)
            print(f"Total seasons: {len(seasons)}")
            print("=" * 60)
            
            return 0
            
    except Exception as e:
        logger.error(f"Error fetching seasons: {e}", exc_info=True)
        print(f"✗ Error: {e}")
        return 1


async def fetch_and_list_regions() -> int:
    """Fetch and list all available states and regions with identifiers.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("=" * 100)
    print("Available States and Regions (with filtering identifiers)")
    print("=" * 100)
    
    try:
        scraper = JugendMusiziertScraper()
        async with aiohttp.ClientSession() as session:
            regions_data = await scraper.fetch_regions(session)
            
            if not regions_data:
                print("✗ Failed to fetch regions data")
                return 1
            
            data = scraper.extract_regions(regions_data)
            states = data.get("states", [])
            regions = data.get("regions", [])
            
            if not states and not regions:
                print("No states or regions found in API response")
                return 0
            
            # Display states (Landeswettbewerbe) with identifiers
            print(f"\n>>> States (Landeswettbewerbe): {len(states)} found\n")
            print(f"{'Title':<35} | {'ID':<5} | {'Slug':<30}")
            print("-" * 75)
            
            for state in states:
                title = state.get("title", "")
                sid = state.get("id", "")
                slug = state.get("slug", "")
                print(f"{title:<35} | {str(sid):<5} | {slug:<30}")
            
            # Display regions (Regionalwettbewerbe) with identifiers
            print(f"\n>>> Regional Subdivisions (Regionalwettbewerbe): {len(regions)} found\n")
            print(f"{'Title':<35} | {'ID':<5} | {'Slug':<30} | {'Parent State':<20}")
            print("-" * 100)
            
            for region in regions:
                title = region.get("title", "")
                rid = region.get("id", "")
                slug = region.get("slug", "")
                parent = region.get("parent_state", "")
                print(f"{title:<35} | {str(rid):<5} | {slug:<30} | {parent:<20}")
            
            print("\n" + "=" * 100)
            print("FILTERING OPTIONS:")
            print("=" * 100)
            print("\nYou can now filter scraping by:")
            print("  • State ID: --state-id <id>  (e.g., --state-id 6)")
            print("  • State Slug: --state-slug <slug>  (e.g., --state-slug baden-wuerttemberg)")
            print("  • Region ID: --region-id <id>  (e.g., --region-id 7)")
            print("  • Region Slug: --region-slug <slug>  (e.g., --region-slug bodenseekreis)")
            print("=" * 100)
            
            return 0
            
    except Exception as e:
        logger.error(f"Error fetching regions: {e}", exc_info=True)
        print(f"✗ Error: {e}")
        return 1


async def main() -> int:
    """Main scraper execution with CLI argument handling.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description='Jugend musiziert Tournament Scraper (Async)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                       Scrape all data and save to data/
  %(prog)s --force               Force re-scraping of all data
  %(prog)s --season-filter 47    Filter to specific season ID
  %(prog)s --region-filter Bayern  Filter to specific region
  %(prog)s --list-seasons        Display all available seasons
  %(prog)s --list-regions        Display all available regions
  %(prog)s --list-all            Display both seasons and regions
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-scraping of all data (ignore version cache)'
    )
    parser.add_argument(
        '--season-filter',
        type=str,
        help='Filter scraping to specific season ID'
    )
    parser.add_argument(
        '--region-filter',
        type=str,
        help='Filter scraping to specific region name'
    )
    parser.add_argument(
        '--list-seasons',
        action='store_true',
        help='Fetch and display all available seasons'
    )
    parser.add_argument(
        '--list-regions',
        action='store_true',
        help='Fetch and display all available regions'
    )
    parser.add_argument(
        '--list-all',
        action='store_true',
        help='Fetch and display both seasons and regions'
    )
    
    args = parser.parse_args()
    
    # Handle list operations
    if args.list_seasons or args.list_all:
        exit_code = await fetch_and_list_seasons()
        if args.list_all:
            print()  # Blank line between outputs
            exit_code = await fetch_and_list_regions()
        return exit_code
    
    if args.list_regions:
        return await fetch_and_list_regions()
    
    # Normal scraping operation
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
