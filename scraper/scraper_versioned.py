"""
Versioned scraper with incremental update support.

Wraps the base scraper with versioning capabilities:
- Detects new seasons and regions
- Only scrapes new data by default
- Supports force re-scraping
- Maintains version history
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from version_manager import VersionManager


logger = logging.getLogger(__name__)


class VersionedScraper:
    """
    Scraper with version management and incremental updates.
    
    Usage:
        scraper = VersionedScraper(base_url, data_dir="data")
        
        # Smart scrape (only new seasons)
        scraper.scrape()
        
        # Force re-scrape specific season
        scraper.scrape(force=True, season_filter=[2025])
        
        # Re-scrape specific region
        scraper.scrape(force=True, region_filter=['Baden-Württemberg'])
    """
    
    def __init__(
        self,
        base_url: str,
        data_dir: Path = Path("data"),
        config: Optional[Dict] = None
    ):
        """
        Initialize versioned scraper.
        
        Args:
            base_url: Base URL for scraping
            data_dir: Root data directory
            config: Configuration dict with scraper settings
        """
        self.base_url = base_url
        self.data_dir = Path(data_dir)
        self.config = config or {}
        
        # Initialize version manager
        self.version_manager = VersionManager(data_dir)
        
        # Note: Import actual scraper after it's updated with versioning support
        # from scraper import JugendMusiziertScraper
        # self.base_scraper = JugendMusiziertScraper(base_url)
    
    def detect_seasons_and_regions(self) -> Dict[str, List]:
        """
        Detect available seasons and regions from website.
        
        Returns:
            Dict with 'seasons' and 'regions' lists
        """
        # TODO: Implement season/region detection from website
        # This should parse the website and extract available seasons
        # and regions without scraping full data
        raise NotImplementedError(
            "Season/region detection needs to be implemented based on website structure"
        )
    
    def scrape(
        self,
        force: bool = False,
        season_filter: Optional[List[int]] = None,
        region_filter: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Scrape tournament data with version management.
        
        Args:
            force: If True, re-scrape all data (default: only new)
            season_filter: Only scrape these seasons (None = all available)
            region_filter: Only scrape these regions (None = all available)
            dry_run: If True, only show what would be scraped (no actual scraping)
            
        Returns:
            Dict with scraping results and version info
        """
        logger.info("Starting versioned scrape...")
        
        # Detect available seasons and regions
        detected = self.detect_seasons_and_regions()
        detected_seasons = detected.get("seasons", [])
        detected_regions = detected.get("regions", [])
        
        logger.info(f"Detected {len(detected_seasons)} season(s), {len(detected_regions)} region(s)")
        
        # Determine what should be scraped
        decision = self.version_manager.should_scrape(
            detected_seasons=detected_seasons,
            detected_regions=detected_regions,
            force=force,
            season_filter=season_filter,
            region_filter=region_filter
        )
        
        logger.info(f"Scrape decision: {decision['reason']}")
        
        if not decision["should_scrape"]:
            return {
                "success": False,
                "reason": decision["reason"],
                "data_scraped": False,
                "version_created": False
            }
        
        if dry_run:
            return {
                "success": True,
                "reason": "Dry run",
                "seasons_to_scrape": decision["new_seasons"],
                "regions_to_scrape": decision["new_regions"],
                "data_scraped": False,
                "version_created": False
            }
        
        # Perform actual scraping (TODO: implement in base scraper)
        logger.info(
            f"Scraping {len(decision['new_seasons'])} season(s), "
            f"{len(decision['new_regions'])} region(s)..."
        )
        
        # TODO: Call base scraper with season/region filters
        # scraped_data = self.base_scraper.scrape(
        #     seasons=decision["new_seasons"],
        #     regions=decision["new_regions"]
        # )
        
        scraped_data = {
            "api_endpoints": [],
            "embedded_data": [],
            "metadata": {
                "seasons": decision["new_seasons"],
                "regions": decision["new_regions"]
            }
        }
        
        # Create version
        version_id = self.version_manager.create_version(
            seasons=decision["new_seasons"],
            regions=decision["new_regions"],
            metadata={
                "force": force,
                "dry_run": dry_run
            }
        )
        
        # Save version data
        self.version_manager.save_version_data(version_id, scraped_data)
        
        # Update main data file (latest)
        self._update_main_data_file(scraped_data)
        
        logger.info(f"Scraping complete. Version: {version_id}")
        
        return {
            "success": True,
            "version_id": version_id,
            "seasons_scraped": decision["new_seasons"],
            "regions_scraped": decision["new_regions"],
            "data_scraped": True,
            "version_created": True
        }
    
    def _update_main_data_file(self, data: Dict) -> None:
        """Update the main jugend_musiziert_data.json file with latest data."""
        main_file = self.data_dir / "jugend_musiziert_data.json"
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated main data file: {main_file}")
    
    def get_version_info(self) -> Dict:
        """Get information about all versions."""
        return self.version_manager.get_version_info()
    
    def get_version_data(self, version_id: str) -> Optional[Dict]:
        """Load data from a specific version."""
        return self.version_manager.load_version_data(version_id)
    
    def list_versions(self) -> List[Dict]:
        """List all versions."""
        return self.version_manager.versions.get("versions", [])


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    base_url = "https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan"
    
    scraper = VersionedScraper(base_url, data_dir="data")
    
    # Smart scrape (only new)
    print("\n=== Smart Scrape (default) ===")
    result = scraper.scrape(dry_run=True)
    print(json.dumps(result, indent=2))
    
    # Force scrape with filters
    print("\n=== Force Scrape (2025 season only) ===")
    result = scraper.scrape(force=True, season_filter=[2025], dry_run=True)
    print(json.dumps(result, indent=2))
    
    # Version info
    print("\n=== Version Info ===")
    info = scraper.get_version_info()
    print(json.dumps(info, indent=2))
