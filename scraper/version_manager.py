"""
Version management system for scraper data.

Tracks which seasons and regions have been scraped, enabling:
- Incremental scraping (only new seasons by default)
- Season/region detection
- Force re-scraping with version control
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set


class VersionManager:
    """Manages scraper versions and incremental data updates."""
    
    def __init__(self, data_dir: Path = Path("data")):
        """
        Initialize version manager.
        
        Args:
            data_dir: Root data directory for storing versions
        """
        self.data_dir = Path(data_dir)
        self.versions_dir = self.data_dir / "versions"
        self.version_index_path = self.data_dir / "versions.json"
        
        # Create directories
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create version index
        self.versions = self._load_version_index()
    
    def _load_version_index(self) -> Dict:
        """Load version index from disk."""
        if self.version_index_path.exists():
            with open(self.version_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"versions": []}
    
    def _save_version_index(self) -> None:
        """Save version index to disk."""
        with open(self.version_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.versions, f, indent=2, ensure_ascii=False)
    
    def create_version(
        self,
        seasons: Optional[List[int]] = None,
        regions: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new version snapshot.
        
        Args:
            seasons: List of season IDs in this version
            regions: List of region identifiers in this version
            metadata: Additional metadata
            
        Returns:
            Version ID (Unix timestamp in seconds)
        """
        version_id = str(int(time.time()))
        
        version_record = {
            "version_id": version_id,
            "timestamp": datetime.utcnow().isoformat(),
            "seasons": seasons or [],
            "regions": regions or [],
            "metadata": metadata or {},
            "data_file": f"v{version_id}.json"
        }
        
        self.versions["versions"].append(version_record)
        self._save_version_index()
        
        return version_id
    
    def get_latest_version(self) -> Optional[Dict]:
        """Get the latest version record."""
        if self.versions["versions"]:
            return self.versions["versions"][-1]
        return None
    
    def get_scraped_seasons(self) -> Set[int]:
        """Get all seasons that have been scraped."""
        seasons = set()
        for version in self.versions["versions"]:
            seasons.update(version.get("seasons", []))
        return seasons
    
    def get_scraped_regions(self) -> Set[str]:
        """Get all regions that have been scraped."""
        regions = set()
        for version in self.versions["versions"]:
            regions.update(version.get("regions", []))
        return regions
    
    def should_scrape(
        self,
        detected_seasons: List[int],
        detected_regions: List[str],
        force: bool = False,
        season_filter: Optional[List[int]] = None,
        region_filter: Optional[List[str]] = None
    ) -> Dict:
        """
        Determine what should be scraped.
        
        Args:
            detected_seasons: Seasons available on website
            detected_regions: Regions available on website
            force: If True, re-scrape everything
            season_filter: Only scrape these seasons (None = all)
            region_filter: Only scrape these regions (None = all)
            
        Returns:
            Dict with:
                - should_scrape: bool
                - new_seasons: list of seasons to scrape
                - new_regions: list of regions to scrape
                - reason: explanation of decision
        """
        if force:
            # Force mode: scrape everything
            seasons_to_scrape = (
                season_filter if season_filter
                else detected_seasons
            )
            regions_to_scrape = (
                region_filter if region_filter
                else detected_regions
            )
            return {
                "should_scrape": True,
                "new_seasons": seasons_to_scrape,
                "new_regions": regions_to_scrape,
                "reason": "Force mode enabled - re-scraping all data"
            }
        
        # Default mode: only scrape new seasons/regions
        scraped_seasons = self.get_scraped_seasons()
        scraped_regions = self.get_scraped_regions()
        
        # Determine what's new
        all_new_seasons = [
            s for s in detected_seasons
            if s not in scraped_seasons
        ]
        all_new_regions = [
            r for r in detected_regions
            if r not in scraped_regions
        ]
        
        # Apply filters
        new_seasons = all_new_seasons
        new_regions = all_new_regions
        
        if season_filter:
            new_seasons = [s for s in new_seasons if s in season_filter]
        if region_filter:
            new_regions = [r for r in new_regions if r in region_filter]
        
        has_new_seasons = len(new_seasons) > 0
        has_new_regions = len(new_regions) > 0
        
        if not has_new_seasons and not has_new_regions:
            return {
                "should_scrape": False,
                "new_seasons": [],
                "new_regions": [],
                "reason": "No new seasons or regions detected"
            }
        
        return {
            "should_scrape": True,
            "new_seasons": new_seasons,
            "new_regions": new_regions,
            "reason": f"New data detected - {len(new_seasons)} season(s), {len(new_regions)} region(s)"
        }
    
    def get_version_path(self, version_id: str) -> Path:
        """Get the file path for a version."""
        return self.versions_dir / f"v{version_id}.json"
    
    def load_version_data(self, version_id: str) -> Optional[Dict]:
        """Load data for a specific version."""
        version_path = self.get_version_path(version_id)
        if version_path.exists():
            with open(version_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_version_data(self, version_id: str, data: Dict) -> None:
        """Save data for a version."""
        version_path = self.get_version_path(version_id)
        with open(version_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_version_info(self) -> Dict:
        """Get summary information about all versions."""
        return {
            "total_versions": len(self.versions["versions"]),
            "latest_version": self.get_latest_version(),
            "scraped_seasons": sorted(self.get_scraped_seasons()),
            "scraped_regions": sorted(self.get_scraped_regions()),
            "versions": self.versions["versions"]
        }
