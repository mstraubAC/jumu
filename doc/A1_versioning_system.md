# A1. Versioning System

Complete technical guide to the data versioning system for safe, incremental scraping.

## Architecture

```
data/
├── jugend_musiziert_data.json     # Latest data (always current)
├── versions.json                   # Version index and history
└── versions/
    ├── v1706604000.json           # Version 1 (timestamp-based)
    ├── v1706690400.json           # Version 2
    └── ...
```

## Version Structure

Each version is identified by a **Unix timestamp** (seconds precision):

```json
{
  "version_id": "1706604000",
  "timestamp": "2024-01-30T12:00:00",
  "seasons": [2024, 2025],
  "regions": ["Baden-Württemberg", "Bayern"],
  "metadata": {
    "force": false,
    "dry_run": false
  },
  "data_file": "v1706604000.json"
}
```

## Smart Scraping (Default)

Only scrapes new seasons/regions detected since last run:

```python
from scraper.scraper_versioned import VersionedScraper

scraper = VersionedScraper(base_url="...", data_dir="data")
result = scraper.scrape()  # Only scrapes new seasons
```

## Force Re-scrape

Re-scrape everything or with specific filters:

```python
# Re-scrape everything
scraper.scrape(force=True)

# Re-scrape specific season
scraper.scrape(force=True, season_filter=[2025])

# Re-scrape specific region
scraper.scrape(force=True, region_filter=["Bayern"])

# Combined filters
scraper.scrape(force=True, season_filter=[2025], region_filter=["Bayern"])
```

## Filtering Options

```bash
# Scrape only specific seasons or regions
uv run scraper/scraper.py --season-filter=2024,2025
uv run scraper/scraper.py --region-filter=Bayern
uv run scraper/scraper.py --season-filter=2024 --region-filter=Bayern
```

## Decision Logic

```
IF --force:
    Scrape everything
ELIF --season-filter or --region-filter:
    Scrape only matching data
ELIF smart_scraping enabled (default):
    Scrape only new seasons/regions
ELSE:
    Scrape all data
```

## Dry Run Mode

Preview what would be scraped without making changes:

```bash
uv run scraper/scraper.py --dry-run
```

Shows:
- Available seasons on website
- Available regions
- What would be scraped with current settings
- Estimated time and data size

## Implementation

### Core Modules

**scraper/version_manager.py** (197 lines)
- Manages version history and metadata
- Detects new seasons/regions
- Determines what should be scraped
- Loads/saves versioned data

**scraper/scraper_versioned.py** (247 lines)
- Wraps base scraper with version support
- Implements smart scraping logic
- Supports force re-scraping with filters
- Main entry point for versioned scraping

**scraper/examples_versioning.py** (149 lines)
- Usage examples and demonstrations
- Run: `python scraper/examples_versioning.py`

## Recovery from Version

Restore data from a previous version:

```bash
# List available versions
cat data/versions.json

# Restore from snapshot
cp data/versions/v{timestamp}.json data/jugend_musiziert_data.json
```

## API Endpoints

The scraper directly calls three main API endpoints:

### 1. Seasons Endpoint
- **URL**: `https://api.jugend-musiziert.org/api/seasons`
- **Method**: `fetch_seasons()`
- **Data**: Tournament seasons (years, age groups, registration deadlines)

### 2. Timetable Endpoint
- **URL**: `https://api.jugend-musiziert.org/api/timetable`
- **Method**: `fetch_timetable()`
- **Data**: Tournament timetable with dates, venues, programs, performers

### 3. Results Endpoint
- **URL Pattern**: `https://www.jugend-musiziert.org/_next/data/{buildId}/de/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/{region_slug}/ergebnisse.json`
- **Method**: `fetch_results_for_region(region_slug)`
- **Feature**: Automatically extracts build ID from main page

## References

- [VersionManager class](../scraper/version_manager.py)
- [VersionedScraper class](../scraper/scraper_versioned.py)
- [Usage examples](../scraper/examples_versioning.py)


