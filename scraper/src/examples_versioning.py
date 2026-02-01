"""
Quick examples of using the versioned scraper.

Run this file to see the versioning system in action.
"""

import json
import sys
from pathlib import Path

# Add scraper to path
sys.path.insert(0, str(Path(__file__).parent))

from version_manager import VersionManager
from scraper_versioned import VersionedScraper


def example_version_manager():
    """Example: Using VersionManager directly."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Version Manager")
    print("="*60)
    
    vm = VersionManager(data_dir="../data")
    
    # Create a version
    print("\nCreating first version...")
    v1 = vm.create_version(
        seasons=[2024],
        regions=["Baden-Württemberg"]
    )
    print(f"✓ Created version: {v1}")
    
    # Create another version
    print("\nCreating second version...")
    v2 = vm.create_version(
        seasons=[2024, 2025],
        regions=["Baden-Württemberg", "Bayern"]
    )
    print(f"✓ Created version: {v2}")
    
    # Get version info
    print("\nVersion Information:")
    info = vm.get_version_info()
    print(f"  Total versions: {info['total_versions']}")
    print(f"  Scraped seasons: {info['scraped_seasons']}")
    print(f"  Scraped regions: {info['scraped_regions']}")


def example_scrape_decision():
    """Example: Decision logic for smart scraping."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Scrape Decision Logic")
    print("="*60)
    
    vm = VersionManager(data_dir="../data")
    
    # Scenario 1: First scrape
    print("\nScenario 1: First scrape (nothing scraped yet)")
    decision = vm.should_scrape(
        detected_seasons=[2024, 2025],
        detected_regions=["Baden-Württemberg", "Bayern"]
    )
    print(f"  Decision: {decision['reason']}")
    print(f"  New seasons: {decision['new_seasons']}")
    print(f"  New regions: {decision['new_regions']}")
    
    # Scenario 2: Second scrape with some overlapping data
    print("\nScenario 2: Already have 2024, new is 2025")
    decision = vm.should_scrape(
        detected_seasons=[2024, 2025],
        detected_regions=["Baden-Württemberg"]
    )
    print(f"  Decision: {decision['reason']}")
    print(f"  New seasons: {decision['new_seasons']}")
    
    # Scenario 3: No new data
    print("\nScenario 3: No new data (everything already scraped)")
    decision = vm.should_scrape(
        detected_seasons=[2024, 2025],
        detected_regions=["Baden-Württemberg", "Bayern"]
    )
    print(f"  Decision: {decision['reason']}")
    print(f"  Should scrape: {decision['should_scrape']}")
    
    # Scenario 4: Force scrape with filters
    print("\nScenario 4: Force scrape season 2024 only")
    decision = vm.should_scrape(
        detected_seasons=[2024, 2025],
        detected_regions=["Baden-Württemberg", "Bayern"],
        force=True,
        season_filter=[2024]
    )
    print(f"  Decision: {decision['reason']}")
    print(f"  Seasons to scrape: {decision['new_seasons']}")
    print(f"  Regions to scrape: {decision['new_regions']}")


def example_versioned_scraper():
    """Example: Using VersionedScraper with dry run."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Versioned Scraper (Dry Run)")
    print("="*60)
    
    scraper = VersionedScraper(
        base_url="https://...",
        data_dir="../data"
    )
    
    # Note: This will fail because detect_seasons_and_regions() is not implemented
    # This is just to show the intended usage
    
    print("\nIntended usage:")
    print("  scraper.scrape()  # Smart scrape - only new data")
    print("  scraper.scrape(force=True)  # Force scrape all")
    print("  scraper.scrape(force=True, season_filter=[2025])  # Force scrape specific season")
    print("  scraper.scrape(force=True, dry_run=True)  # Preview without scraping")
    
    # Show version info
    print("\nVersion info:")
    info = scraper.get_version_info()
    print(json.dumps(info, indent=2))


def example_workflow():
    """Example: Typical scraping workflow."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Typical Workflow")
    print("="*60)
    
    print("""
1. INITIAL SCRAPE (get all data)
   scraper.scrape()
   → Detects 2024, 2025 seasons
   → Creates version v1
   → Saves to data/versions/v1.json
   → Updates data/jugend_musiziert_data.json

2. DAILY RUN (only new data)
   scraper.scrape()  # Tomorrow
   → No new seasons
   → Skips (no version created)

3. NEW SEASON DETECTED (automatic)
   scraper.scrape()  # In 2 weeks
   → Season 2026 available
   → Creates version v2
   → Saves new data

4. MISSED A SEASON (manual fix)
   scraper.scrape(force=True, season_filter=[2024])
   → Re-scrapes season 2024
   → Creates version v3
   → Updates data file

5. REGION-SPECIFIC UPDATE
   scraper.scrape(force=True, region_filter=["Bayern"])
   → Re-scrapes Bayern region
   → Creates version v4

6. VIEW VERSION HISTORY
   info = scraper.get_version_info()
   → Shows all versions with timestamps
   → Lists which seasons/regions in each
    """)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VERSIONED SCRAPER EXAMPLES")
    print("="*60)
    
    try:
        example_version_manager()
    except FileNotFoundError:
        print("Note: Run from scraper/ directory for examples to work")
    
    try:
        example_scrape_decision()
    except Exception as e:
        print(f"Could not run example: {e}")
    
    example_versioned_scraper()
    example_workflow()
    
    print("\n" + "="*60)
    print("For detailed documentation, see: scraper/VERSIONING.md")
    print("="*60)
