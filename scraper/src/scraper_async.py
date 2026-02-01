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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

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
    
    API Flow (from doc/human_notes/analysis_of_jumu_webpage_data.md):
    1. Fetch seasons: /api/seasons?order[year]=desc
    2. Fetch regions from Next.js page data (sideMenu hierarchy)
    3. For each region, fetch its page to get contestIdentifier
    4. Fetch timetable filtered by contest.identifier and contest.season.id
    5. Optionally fetch contest details via /api/currentContest/{identifier}
    """
    
    # API endpoints
    API_BASE: str = "https://api.jugend-musiziert.org/api"
    SEASONS_ENDPOINT: str = f"{API_BASE}/seasons?order[year]=desc"
    TIMETABLE_ENDPOINT: str = f"{API_BASE}/timetable"
    CURRENT_CONTEST_ENDPOINT: str = f"{API_BASE}/currentContest"  # + /{identifier}
    
    # Next.js data endpoints (website frontend)
    NEXTJS_BASE: str = "https://www.jugend-musiziert.org/_next/data"
    # Build ID changes periodically - we'll extract it dynamically
    REGIONS_ENDPOINT: str = "https://www.jugend-musiziert.org/_next/data/gk2cuCjnn0VZy0e6OaBbU/de/wettbewerbe/regionalwettbewerbe.json"
    
    # Request configuration
    TIMEOUT: int = 30  # seconds (increased for pagination)
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
        
        Endpoint: /api/seasons?order[year]=desc
        
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
    
    async def fetch_current_contest(
        self,
        session: aiohttp.ClientSession,
        contest_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch current contest details by identifier.
        
        Endpoint: /api/currentContest/{identifier}
        Example: /api/currentContest/BaWue_Esslingen
        
        Args:
            session: aiohttp ClientSession for connection reuse.
            contest_identifier: Contest identifier (e.g., 'BaWue_Esslingen').
        
        Returns:
            Contest data dictionary or None if request fails.
        """
        url = f"{self.CURRENT_CONTEST_ENDPOINT}/{contest_identifier}"
        logger.info(f"Fetching current contest: {contest_identifier}")
        data = await self._make_request(session, url)
        if data:
            logger.info(f"Successfully fetched contest data for {contest_identifier}")
        return data
    
    async def fetch_region_page(
        self,
        session: aiohttp.ClientSession,
        region_link: str,
        build_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch a region's page data to extract contestIdentifier.
        
        The contestIdentifier is stored in pageProps.page.meta.contestIdentifier.
        
        Args:
            session: aiohttp ClientSession for connection reuse.
            region_link: Region page link (e.g., '/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr').
            build_id: Next.js build ID (uses default if not provided).
        
        Returns:
            Page data dictionary or None if request fails.
        """
        # Use provided build_id or extract from REGIONS_ENDPOINT
        if not build_id:
            # Extract build_id from the known endpoint
            build_id = self.REGIONS_ENDPOINT.split("/data/")[1].split("/")[0]
        
        # Construct the Next.js data URL
        # e.g., /_next/data/{buildId}/de{region_link}.json
        page_path = region_link.rstrip("/")
        if not page_path.endswith("/zeitplan"):
            page_path = f"{page_path}/zeitplan"
        
        url = f"{self.NEXTJS_BASE}/{build_id}/de{page_path}.json"
        
        # Add slug query params
        slugs = page_path.strip("/").split("/")
        slug_params = "&".join([f"slug={s}" for s in slugs])
        url = f"{url}?{slug_params}"
        
        logger.debug(f"Fetching region page: {url}")
        data = await self._make_request(session, url)
        return data
    
    def extract_contest_identifier(self, page_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract contestIdentifier from a region page's data.
        
        Args:
            page_data: Page data from fetch_region_page.
        
        Returns:
            Contest identifier string or None if not found.
        """
        if not page_data:
            return None
        
        try:
            return page_data.get("pageProps", {}).get("page", {}).get("meta", {}).get("contestIdentifier")
        except (KeyError, TypeError):
            return None
    
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
    
    async def fetch_timetable_filtered(
        self,
        session: aiohttp.ClientSession,
        contest_identifier: str,
        season_id: Optional[str] = None,
        items_per_page: int = 100
    ) -> Optional[Dict[str, Any]]:
        """Fetch timetable filtered by contest identifier and optionally season.
        
        This is the preferred method for fetching timetable data for a specific
        region/contest. Uses the documented API filters:
        - contest.identifier: The contest identifier (e.g., 'BaWue_Esslingen')
        - contest.season.id: The season ID (use -1 for current season, or specific ID)
        
        Endpoint: /api/timetable?contest.identifier={identifier}&contest.season.id={season_id}
        
        Args:
            session: aiohttp ClientSession for connection reuse.
            contest_identifier: Contest identifier (e.g., 'BaWue_Esslingen').
            season_id: Season ID to filter by (use '-1' for current, or specific ID like '3').
            items_per_page: Number of items per page (default 100 for efficiency).
        
        Returns:
            Combined timetable data or None if request fails.
        """
        # Build URL with filters
        params = [f"itemsPerPage={items_per_page}"]
        params.append(f"contest.identifier={contest_identifier}")
        
        if season_id:
            params.append(f"contest.season.id={season_id}")
        
        base_url = f"{self.TIMETABLE_ENDPOINT}?{'&'.join(params)}"
        
        logger.info(f"Fetching filtered timetable for {contest_identifier} (season: {season_id or 'all'})")
        
        all_entries: list = []
        page_count: int = 0
        next_url: Optional[str] = base_url
        
        while next_url:
            page_count += 1
            logger.debug(f"Fetching timetable page {page_count}")
            
            data = await self._make_request(session, next_url)
            if not data:
                logger.warning(f"Failed to fetch page {page_count} for {contest_identifier}")
                break
            
            # Collect entries from this page
            members: list = data.get("hydra:member", [])
            all_entries.extend(members)
            
            # Check for next page
            view: Dict[str, Any] = data.get("hydra:view", {})
            next_url = view.get("hydra:next")
            
            if next_url and next_url.startswith("/"):
                next_url = f"https://api.jugend-musiziert.org{next_url}"
        
        logger.info(
            f"Fetched {len(all_entries)} timetable entries for {contest_identifier} "
            f"({page_count} pages)"
        )
        
        # Return combined data
        result: Dict[str, Any] = {
            "@context": "/api/contexts/TimetableGroup",
            "@id": f"/api/timetable?contest.identifier={contest_identifier}",
            "@type": "hydra:Collection",
            "hydra:member": all_entries,
            "hydra:totalItems": len(all_entries),
            "meta": {
                "contest_identifier": contest_identifier,
                "season_id": season_id,
                "pages_fetched": page_count,
            }
        }
        
        return result
    
    async def fetch_regions_with_identifiers(
        self,
        session: aiohttp.ClientSession,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Fetch regions and populate contest identifiers by fetching each region's page.
        
        This method:
        1. Fetches the main regions page to get the hierarchy
        2. Fetches each region's zeitplan page to extract contestIdentifier
        3. Returns enriched regions data with contest_identifier populated
        
        Args:
            session: aiohttp ClientSession for connection reuse.
            max_concurrent: Maximum concurrent requests (to avoid rate limiting).
        
        Returns:
            Dictionary with 'states' and 'regions' lists, with contest_identifier populated.
        """
        # First, get the basic regions structure
        regions_data = await self.fetch_regions(session)
        if not regions_data:
            return {"states": [], "regions": []}
        
        # Extract basic structure
        data = self.extract_regions(regions_data)
        regions = data.get("regions", [])
        
        logger.info(f"Fetching contest identifiers for {len(regions)} regions...")
        
        # Fetch each region's page to get contest identifier
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_identifier(region: Dict[str, Any]) -> None:
            async with semaphore:
                link = region.get("link", "")
                if link:
                    page_data = await self.fetch_region_page(session, link)
                    identifier = self.extract_contest_identifier(page_data)
                    region["contest_identifier"] = identifier
                    if identifier:
                        logger.debug(f"  {region['title']}: {identifier}")
                    else:
                        logger.warning(f"  {region['title']}: No contest identifier found")
        
        # Fetch all identifiers concurrently (with limit)
        await asyncio.gather(*[fetch_identifier(r) for r in regions])
        
        # Count successful extractions
        with_identifier = sum(1 for r in regions if r.get("contest_identifier"))
        logger.info(f"Found contest identifiers for {with_identifier}/{len(regions)} regions")
        
        data["regions"] = regions
        return data
    
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
    
    async def scrape(
        self,
        season_id: Optional[str] = None,
        contest_identifiers: Optional[List[str]] = None,
        fetch_all_timetables: bool = False
    ) -> Dict[str, Any]:
        """Scrape tournament data with optional filtering.
        
        Flow:
        1. Fetch seasons (always)
        2. Fetch regions with contest identifiers
        3. Fetch timetables (filtered by contest_identifiers if provided)
        
        Args:
            season_id: Filter to specific season ID (use '-1' for current season).
            contest_identifiers: List of contest identifiers to fetch timetables for.
                                If None and fetch_all_timetables=False, fetches only metadata.
            fetch_all_timetables: If True, fetches timetables for all discovered regions.
        
        Returns:
            Dictionary containing: seasons, regions, timetables (per contest).
        """
        async with aiohttp.ClientSession() as session:
            # Step 1: Fetch seasons
            logger.info("Step 1/3: Fetching seasons...")
            seasons = await self.fetch_seasons(session)
            
            # Step 2: Fetch regions with contest identifiers
            logger.info("Step 2/3: Fetching regions with contest identifiers...")
            regions_data = await self.fetch_regions_with_identifiers(session)
            
            # Step 3: Fetch timetables based on mode
            timetables: Dict[str, Any] = {}
            
            if contest_identifiers:
                # Fetch specific contest timetables
                logger.info(f"Step 3/3: Fetching timetables for {len(contest_identifiers)} contests...")
                for identifier in contest_identifiers:
                    timetable = await self.fetch_timetable_filtered(
                        session, identifier, season_id
                    )
                    if timetable:
                        timetables[identifier] = timetable
                        
            elif fetch_all_timetables:
                # Fetch timetables for all regions with identifiers
                regions = regions_data.get("regions", [])
                identifiers = [r["contest_identifier"] for r in regions if r.get("contest_identifier")]
                logger.info(f"Step 3/3: Fetching timetables for all {len(identifiers)} contests...")
                
                for identifier in identifiers:
                    timetable = await self.fetch_timetable_filtered(
                        session, identifier, season_id
                    )
                    if timetable:
                        timetables[identifier] = timetable
            else:
                # Legacy mode: fetch all timetables without filtering
                logger.info("Step 3/3: Fetching all timetables (unfiltered)...")
                all_timetable = await self.fetch_timetable(session, season_id)
                if all_timetable:
                    timetables["_all"] = all_timetable
            
            data: Dict[str, Any] = {
                'seasons': seasons,
                'regions': regions_data,
                'timetables': timetables,
            }
            
            return data
    
    async def scrape_contest(
        self,
        contest_identifier: str,
        season_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scrape data for a single contest/region.
        
        Convenience method for fetching all data related to a specific contest.
        
        Args:
            contest_identifier: Contest identifier (e.g., 'BaWue_Esslingen').
            season_id: Filter to specific season ID (use '-1' for current season).
        
        Returns:
            Dictionary containing: contest_info, timetable.
        """
        async with aiohttp.ClientSession() as session:
            # Fetch contest info and timetable in parallel
            contest_task = self.fetch_current_contest(session, contest_identifier)
            timetable_task = self.fetch_timetable_filtered(session, contest_identifier, season_id)
            
            contest_info, timetable = await asyncio.gather(
                contest_task,
                timetable_task,
                return_exceptions=False
            )
            
            return {
                'contest_identifier': contest_identifier,
                'contest_info': contest_info,
                'timetable': timetable,
            }
    
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
    console = Console()
    
    try:
        scraper = JugendMusiziertScraper()
        async with aiohttp.ClientSession() as session:
            seasons_data = await scraper.fetch_seasons(session)
            
            if not seasons_data:
                console.print("[red]✗ Failed to fetch seasons data[/red]")
                return 1
            
            seasons = scraper.extract_seasons(seasons_data)
            
            if not seasons:
                console.print("No seasons found in API response")
                return 0
            
            members = seasons_data.get('hydra:member', [])
            
            # Create table
            table = Table(title="Available Seasons")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Year", justify="center", style="green")
            
            for member in members:
                season_id = member.get("@id", "").split("/")[-1]
                year = str(member.get("year", "N/A"))
                table.add_row(season_id, year)
            
            console.print(table)
            console.print(f"\n[bold]Total seasons:[/bold] {len(seasons)}")
            
            return 0
            
    except Exception as e:
        logger.error(f"Error fetching seasons: {e}", exc_info=True)
        console.print(f"[red]✗ Error: {e}[/red]")
        return 1


async def fetch_and_list_regions() -> int:
    """Fetch and list all available states and regions with contest identifiers.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    console = Console()
    
    try:
        scraper = JugendMusiziertScraper()
        async with aiohttp.ClientSession() as session:
            console.print("\n[dim]Fetching contest identifiers for each region (this may take a moment)...[/dim]")
            data = await scraper.fetch_regions_with_identifiers(session)
            
            states = data.get("states", [])
            regions = data.get("regions", [])
            
            if not states and not regions:
                console.print("No states or regions found in API response")
                return 0
            
            # States table
            states_table = Table(title=f"States (Landeswettbewerbe) - {len(states)} found")
            states_table.add_column("Title", style="cyan")
            states_table.add_column("ID", justify="right", style="dim")
            states_table.add_column("Slug", style="green")
            
            for state in states:
                states_table.add_row(
                    state.get("title", ""),
                    str(state.get("id", "")),
                    state.get("slug", "")
                )
            
            console.print(states_table)
            
            # Regions table
            regions_table = Table(title=f"Regional Subdivisions (Regionalwettbewerbe) - {len(regions)} found")
            regions_table.add_column("Title", style="cyan")
            regions_table.add_column("Contest Identifier", style="bold green")
            regions_table.add_column("Parent State", style="dim")
            
            for region in regions:
                identifier = region.get("contest_identifier", "") or "[red](not found)[/red]"
                regions_table.add_row(
                    region.get("title", ""),
                    identifier,
                    region.get("parent_state", "")
                )
            
            console.print(regions_table)
            
            # Summary
            with_id = sum(1 for r in regions if r.get("contest_identifier"))
            console.print(f"\n[green]✓[/green] {with_id}/{len(regions)} regions have contest identifiers")
            
            # Usage panel
            usage_text = (
                "[bold]To scrape a specific contest by identifier:[/bold]\n"
                "  uv run scraper/scraper.py --contest BaWue_Esslingen\n"
                "  uv run scraper/scraper.py --contest BaWue_Esslingen --season 3"
            )
            console.print(Panel(usage_text, title="Usage", border_style="blue"))
            
            return 0
            
    except Exception as e:
        logger.error(f"Error fetching regions: {e}", exc_info=True)
        console.print(f"[red]✗ Error: {e}[/red]")
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
  %(prog)s                            Scrape all data (seasons, regions, all timetables)
  %(prog)s --contest BaWue_Esslingen  Scrape specific contest by identifier
  %(prog)s --contest BaWue_Esslingen --season 3   Scrape contest for specific season
  %(prog)s --season 3                 Filter all timetables to season ID 3
  %(prog)s --season -1                Use current season (season.id = -1)
  %(prog)s --list-seasons             Display all available seasons
  %(prog)s --list-regions             Display all regions with contest identifiers
        """
    )
    
    # Scraping options
    parser.add_argument(
        '--contest',
        type=str,
        metavar='IDENTIFIER',
        help='Scrape specific contest by identifier (e.g., BaWue_Esslingen)'
    )
    parser.add_argument(
        '--season',
        type=str,
        metavar='ID',
        help='Filter to specific season ID (use -1 for current season)'
    )
    parser.add_argument(
        '--all-timetables',
        action='store_true',
        help='Fetch timetables for all discovered regions (slow)'
    )
    
    # List options
    parser.add_argument(
        '--list-seasons',
        action='store_true',
        help='Fetch and display all available seasons'
    )
    parser.add_argument(
        '--list-regions',
        action='store_true',
        help='Fetch and display all regions with contest identifiers'
    )
    parser.add_argument(
        '--list-all',
        action='store_true',
        help='Fetch and display both seasons and regions'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        type=str,
        metavar='FILE',
        help='Output file path (default: data/jugend_musiziert_data.json)'
    )
    
    args = parser.parse_args()
    
    console = Console()
    
    # Handle list operations
    if args.list_seasons or args.list_all:
        exit_code = await fetch_and_list_seasons()
        if args.list_all:
            console.print()  # Blank line between outputs
            exit_code = await fetch_and_list_regions()
        return exit_code
    
    if args.list_regions:
        return await fetch_and_list_regions()
    
    # Normal scraping operation
    console.print(Panel.fit(
        "[bold]Jugend musiziert Tournament Scraper[/bold] (Async)",
        border_style="blue"
    ))
    
    try:
        logger.info("Starting scraper...")
        
        # Initialize scraper
        scraper = JugendMusiziertScraper()
        
        # Determine scraping mode
        contest_identifiers = [args.contest] if args.contest else None
        
        if args.contest:
            # Single contest mode
            console.print(f"[dim]Scraping single contest:[/dim] [cyan]{args.contest}[/cyan]")
            all_data = await scraper.scrape_contest(
                contest_identifier=args.contest,
                season_id=args.season
            )
        else:
            # Full scrape mode
            console.print("[dim]Scraping all data...[/dim]")
            all_data = await scraper.scrape(
                season_id=args.season,
                contest_identifiers=contest_identifiers,
                fetch_all_timetables=args.all_timetables
            )
        
        # Add metadata
        import datetime
        all_data['metadata'] = {
            'timestamp': datetime.datetime.now().isoformat(),
            'api_base': JugendMusiziertScraper.API_BASE,
            'season_filter': args.season,
            'contest_filter': args.contest,
        }
        
        # Save to file
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        if args.output:
            output_file = Path(args.output)
        elif args.contest:
            output_file = data_dir / f'{args.contest}.json'
        else:
            output_file = data_dir / 'jugend_musiziert_data.json'
        
        scraper.save_data(all_data, str(output_file))
        
        # Print summary
        summary_table = Table(title="Scraping Summary", show_header=False)
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Item")
        summary_table.add_column("Details", style="dim")
        
        seasons_data = all_data.get('seasons')
        regions_data = all_data.get('regions', {})
        timetables_data = all_data.get('timetables', {})
        
        if seasons_data:
            season_count = len(seasons_data.get('hydra:member', []))
            summary_table.add_row("✓", "Seasons", f"{season_count} found")
        elif 'contest_info' in all_data:
            summary_table.add_row("✓", "Contest", args.contest)
        else:
            summary_table.add_row("[red]✗[/red]", "Seasons", "[red]Failed to fetch[/red]")
        
        if regions_data:
            region_count = len(regions_data.get('regions', []))
            with_id = sum(1 for r in regions_data.get('regions', []) if r.get('contest_identifier'))
            summary_table.add_row("✓", "Regions", f"{region_count} found ({with_id} with identifiers)")
        
        if timetables_data:
            for identifier, timetable in timetables_data.items():
                entry_count = len(timetable.get('hydra:member', []))
                if identifier == '_all':
                    summary_table.add_row("✓", "Timetable (all)", f"{entry_count} entries")
                else:
                    summary_table.add_row("✓", f"Timetable ({identifier})", f"{entry_count} entries")
        elif 'timetable' in all_data and all_data['timetable']:
            entry_count = len(all_data['timetable'].get('hydra:member', []))
            summary_table.add_row("✓", "Timetable", f"{entry_count} entries")
        
        summary_table.add_row("✓", "Output", str(output_file))
        
        console.print()
        console.print(summary_table)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]✗ Fatal error: {e}[/red]")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)