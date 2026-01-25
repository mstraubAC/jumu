#!/usr/bin/env python3
"""
Web scraper for Jugend musiziert tournament participants
Scrapes the website and extracts participant data from the API

This scraper identifies and fetches JSON data from the Jugend musiziert website's API,
specifically targeting participant and schedule information for regional competitions.
"""

import requests
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse, parse_qs
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JugendMusiziertScraper:
    """Scraper for Jugend musiziert tournament data"""
    
    # API endpoints
    API_BASE = "https://api.jugend-musiziert.org/api"
    SEASONS_ENDPOINT = f"{API_BASE}/seasons"
    TIMETABLE_ENDPOINT = f"{API_BASE}/timetable"
    NEXT_DATA_BASE = "https://www.jugend-musiziert.org/_next/data"
    
    def __init__(self, base_url: str = None):
        """
        Initialize the scraper
        
        Args:
            base_url: The main page URL (optional, for reference)
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.collected_data = {}
        
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
        Fetch timetable/schedule data from API
        
        Args:
            season_id: Optional season ID to filter by
            
        Returns:
            Timetable data or None if request fails
        """
        try:
            url = self.TIMETABLE_ENDPOINT
            if season_id:
                url = f"{url}?season_id={season_id}"
            
            logger.info(f"Fetching timetable from {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched timetable data")
            return data
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
        print("\n[Step 2] Fetching timetable...")
        logger.info("=" * 60)
        timetable = scraper.fetch_timetable()
        if timetable:
            print(f"✓ Retrieved timetable data")
            if isinstance(timetable, list):
                print(f"  Found {len(timetable)} entries")
            elif isinstance(timetable, dict):
                print(f"  Keys in timetable: {list(timetable.keys())[:5]}")
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
