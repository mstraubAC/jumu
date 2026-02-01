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
from typing import Optional, Dict, Any, Set
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
        
    def fetch_seasons(self) -> Optional[Dict[str, Any]]:
        """
        Fetch seasons data from API
        
        Returns:
            Seasons data or None if request fails
        """
        try:
            logger.info(f"Fetching seasons from {self.SEASONS_ENDPOINT}")
            response = self.session.get(self.SEASONS_ENDPOINT, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched seasons data")
            return data
        except Exception as e:
            logger.error(f"Error fetching seasons: {e}")
            return None
    
    def fetch_timetable(self, season_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch all timetable/schedule data from API (handles pagination)
        
        Args:
            season_id: Optional season ID to filter by
            
        Returns:
            Combined timetable data or None if request fails
        """
        try:
            url = self.TIMETABLE_ENDPOINT
            if season_id:
                url = f"{url}?season_id={season_id}"
            
            logger.info(f"Fetching timetable from {url}")
            all_entries = []
            page_count = 0
            next_url = url
            
            while next_url:
                page_count += 1
                logger.info(f"Fetching timetable page {page_count}: {next_url}")
                
                try:
                    response = self.session.get(next_url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Collect entries from this page
                    if "hydra:member" in data:
                        members = data.get("hydra:member", [])
                        all_entries.extend(members)
                        logger.info(f"  Page {page_count}: Retrieved {len(members)} timetable entries")
                    
                    # Check for next page
                    view = data.get("hydra:view", {})
                    next_url = view.get("hydra:next")
                    
                    if next_url:
                        # Make absolute URL if relative
                        if next_url.startswith("/"):
                            next_url = f"https://api.jugend-musiziert.org{next_url}"
                    
                except Exception as e:
                    logger.error(f"Error fetching timetable page {page_count}: {e}")
                    break
            
            logger.info(f"Successfully fetched {page_count} pages of timetable data ({len(all_entries)} total entries)")
            
            # Return combined data with same structure as first page
            result = {
                "@context": "/api/contexts/TimetableGroup",
                "@id": "/api/timetable",
                "@type": "hydra:Collection",
                "hydra:member": all_entries,
                "hydra:totalItems": len(all_entries),
                "meta": {
                    "pages_fetched": page_count,
                    "total_entries": len(all_entries)
                }
            }
            
            return result
        except Exception as e:
            logger.error(f"Error fetching timetable: {e}")
            return None
    
    def fetch_results_for_region(self, region_slug: str, build_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch results data for a specific region
        
        Args:
            region_slug: The region slug (e.g., 'esslingen-goeppingen-und-rems-murr')
            build_id: The Next.js build ID (extracted automatically if not provided)
            
        Returns:
            Results data or None if request fails
        """
        try:
            # If no build ID provided, try to get it from main page
            if not build_id:
                build_id = self._extract_build_id()
            
            if not build_id:
                logger.warning("No build ID found, trying without it")
                return None
            
            # Construct the Next.js data URL
            slug_params = "slug=wettbewerbe&slug=regionalwettbewerbe&slug=baden-wuerttemberg&slug=" + region_slug + "&slug=ergebnisse"
            url = f"{self.NEXT_DATA_BASE}/{build_id}/de/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/{region_slug}/ergebnisse.json?{slug_params}"
            
            logger.info(f"Fetching results from {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched results for {region_slug}")
            return data
        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            return None
    
    def _extract_build_id(self) -> Optional[str]:
        """
        Extract the Next.js build ID from the main page
        
        Returns:
            Build ID or None if not found
        """
        try:
            if not self.base_url:
                logger.warning("No base URL provided, cannot extract build ID")
                return None
            
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            html = response.text
            
            # Look for Next.js build ID pattern
            import re
            match = re.search(r'/_next/data/([a-zA-Z0-9]+)/', html)
            if match:
                build_id = match.group(1)
                logger.info(f"Extracted build ID: {build_id}")
                return build_id
            
            logger.warning("Could not extract build ID from page")
            return None
        except Exception as e:
            logger.error(f"Error extracting build ID: {e}")
            return None
    

    
    def scrape_tournament_data(self, region_slug: str = None) -> Dict[str, Any]:
        """
        Scrape tournament data from APIs
        
        Args:
            region_slug: Optional region slug to fetch results for
            
        Returns:
            Dictionary containing all scraped data
        """
        data = {
            'timestamp': json.dumps(str(json.dumps({"timestamp": str(__import__("datetime").datetime.now())}))),
            'seasons': self.fetch_seasons(),
            'timetable': self.fetch_timetable(),
        }
        
        if region_slug:
            data['results'] = self.fetch_results_for_region(region_slug)
        
        return data
    

    
    def save_data(self, data: Dict[str, Any], output_file: str = 'jugend_musiziert_data.json'):
        """
        Save scraped data to a JSON file
        
        Args:
            data: Data to save
            output_file: Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Data saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")


def main():
    """Main scraper execution"""
    print("="*60)
    print("Jugend musiziert Tournament Scraper (API-based)")
    print("="*60)
    logger.info("Starting Jugend musiziert scraper...")
    
    try:
        # Regional tournament details
        base_url = "https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan"
        region_slug = "esslingen-goeppingen-und-rems-murr"
        
        # Initialize scraper
        scraper = JugendMusiziertScraper(base_url)
        
        # Step 1: Fetch seasons
        print("\n[Step 1] Fetching seasons...")
        logger.info("=" * 60)
        seasons = scraper.fetch_seasons()
        if seasons:
            print(f"✓ Retrieved seasons data")
            if isinstance(seasons, list):
                print(f"  Found {len(seasons)} seasons")
                for season in seasons[:3]:
                    if isinstance(season, dict):
                        print(f"    - {season.get('id', season.get('name', 'Unknown'))}")
        else:
            print("⚠ No seasons data retrieved")
        
        # Step 2: Fetch timetable
        print("\n[Step 2] Fetching timetable (with pagination)...")
        logger.info("=" * 60)
        timetable = scraper.fetch_timetable()
        if timetable:
            print(f"✓ Retrieved timetable data")
            meta = timetable.get("meta", {})
            if meta:
                pages = meta.get("pages_fetched", 0)
                entries = meta.get("total_entries", 0)
                print(f"  Pages fetched: {pages}")
                print(f"  Total entries: {entries}")
            elif isinstance(timetable, list):
                print(f"  Found {len(timetable)} entries")
            elif isinstance(timetable, dict) and "hydra:member" in timetable:
                print(f"  Found {len(timetable.get('hydra:member', []))} entries")
        else:
            print("⚠ No timetable data retrieved")
        
        # Step 3: Fetch results
        print("\n[Step 3] Fetching results...")
        logger.info("=" * 60)
        results = scraper.fetch_results_for_region(region_slug)
        if results:
            print(f"✓ Retrieved results data for {region_slug}")
            if isinstance(results, dict):
                print(f"  Keys in results: {list(results.keys())[:5]}")
        else:
            print("⚠ No results data retrieved")
        
        # Step 4: Combine and save
        print("\n[Step 4] Saving combined data...")
        logger.info("=" * 60)
        
        all_data = {
            'metadata': {
                'timestamp': str(__import__("datetime").datetime.now()),
                'url': base_url,
                'region': region_slug,
                'api_endpoints': {
                    'seasons': JugendMusiziertScraper.SEASONS_ENDPOINT,
                    'timetable': JugendMusiziertScraper.TIMETABLE_ENDPOINT,
                }
            },
            'seasons': seasons,
            'timetable': timetable,
            'results': results,
        }
        
        scraper.save_data(all_data, 'jugend_musiziert_data.json')
        
        # Print summary
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"✓ Seasons data: {'Retrieved' if seasons else 'Failed'}")
        print(f"✓ Timetable data: {'Retrieved' if timetable else 'Failed'}")
        print(f"✓ Results data: {'Retrieved' if results else 'Failed'}")
        print(f"✓ Data saved to: jugend_musiziert_data.json")
        print("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
