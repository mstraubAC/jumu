# A1. Versioning System

Complete guide to the data versioning system for safe, incremental scraping.

## Overview

The versioning system prevents accidental re-scraping of known data by tracking which seasons and regions have been scraped with Unix timestamp precision.

## Smart Scraping

**Default behavior**: Only scrapes new seasons/regions detected since last run.

```bash
uv run scraper/scraper.py          # Smart mode (incremental)
uv run scraper/scraper.py --force  # Force full re-scrape
```

## Version Structure

```json
{
  "version_id": 1706775000,
  "timestamp": "2026-01-31T14:23:00Z",
  "seasons": [2023, 2024, 2025],
  "regions": ["Bayern", "Hessen"],
  "item_counts": {
    "seasons": 28,
    "timetables": 1247,
    "participants": 3891
  }
}
```

## Filtering Options

Scrape only specific seasons or regions:

```bash
# By season
uv run scraper/scraper.py --season-filter=2024,2025

# By region
uv run scraper/scraper.py --region-filter=Bayern

# Combined
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

## Version Files

```
data/
├── jugend_musiziert_data.json      # Current master dataset
├── versions.json                   # Version index
└── versions/
    ├── v1706775000.json            # Snapshot from 2026-01-31 14:23:00 UTC
    ├── v1706832000.json
    └── ...
```

## Dry Run Mode

Preview what would be scraped without making changes:

```bash
uv run scraper/scraper.py --dry-run
```

Output shows:
- Available seasons on website
- Available regions
- What would be scraped with current settings
- Estimated time and data size

## Integration with Scraper

The `VersionedScraper` class wraps `JugendMusiziertScraper` and handles:

1. **Detection**: `detect_seasons_and_regions()` lists available data
2. **Decision**: `should_scrape()` determines if scraping needed
3. **Filtering**: Pass season/region filters to underlying scraper
4. **Storage**: Automatic snapshot creation after successful scrape
5. **Merge**: Combine new data with existing dataset

## Recovery from Version

Restore data from a previous version:

```bash
# List available versions
cat data/versions.json

# Restore from snapshot
cp data/versions/v{timestamp}.json data/jugend_musiziert_data.json
```

## References

- [VersionManager class](../scraper/version_manager.py)
- [VersionedScraper class](../scraper/scraper_versioned.py)
- [Usage examples](../scraper/examples_versioning.py)

