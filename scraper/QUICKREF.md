# Quick Reference: Versioned Scraping

## One-Minute Overview

The versioning system lets you **scrape only new data by default** while maintaining a complete history of all scrapes.

## Common Commands

### Smart Scrape (Recommended)
```python
from scraper.scraper_versioned import VersionedScraper

scraper = VersionedScraper(base_url="...", data_dir="data")
result = scraper.scrape()  # Only scrapes new seasons
```

### Force Re-scrape
```python
# Re-scrape everything
scraper.scrape(force=True)

# Re-scrape specific season
scraper.scrape(force=True, season_filter=[2025])

# Re-scrape specific region
scraper.scrape(force=True, region_filter=["Bayern"])

# Both filters combined
scraper.scrape(force=True, season_filter=[2025], region_filter=["Bayern"])
```

### Preview Without Scraping
```python
scraper.scrape(force=True, season_filter=[2025], dry_run=True)
```

### Check Version History
```python
info = scraper.get_version_info()
print(f"Versions: {info['total_versions']}")
print(f"Seasons: {info['scraped_seasons']}")
print(f"Regions: {info['scraped_regions']}")
```

## Decision Logic

| Situation | Command | Result |
|-----------|---------|--------|
| First scrape | `scrape()` | Scrapes all data |
| New season detected | `scrape()` | Scrapes new season only |
| No new data | `scrape()` | Skips (efficient) |
| Want to refresh data | `scrape(force=True)` | Scrapes everything |
| Fix missing season | `scrape(force=True, season_filter=[2024])` | Scrapes only 2024 |
| Update one region | `scrape(force=True, region_filter=["BW"])` | Scrapes only BW |
| Preview action | `scrape(..., dry_run=True)` | Shows what would happen |

## File Locations

```
data/
├── jugend_musiziert_data.json      # Latest data (use this for analysis)
├── versions.json                    # Version history index
└── versions/
    └── v1706604000.json            # Version snapshots

scraper/
├── scraper_versioned.py            # Main versioned scraper
├── version_manager.py              # Version management logic
├── VERSIONING.md                   # Full documentation
├── IMPLEMENTATION.md               # Implementation details
└── examples_versioning.py          # Usage examples
```

## Configuration (config.json)

```json
{
  "versioning": {
    "enabled": true,           // Turn on/off
    "data_dir": "data",        // Where to store versions
    "smart_scraping": true,    // Only new data by default
    "force_scrape": false,     // Default to smart mode
    "season_filter": null,     // Pre-filter seasons (if needed)
    "region_filter": null      // Pre-filter regions (if needed)
  }
}
```

## Return Values

All `scrape()` calls return:
```python
{
    "success": true/false,
    "version_id": "1706604000",           # Timestamp of version
    "seasons_scraped": [2024, 2025],
    "regions_scraped": ["Baden-Württemberg"],
    "data_scraped": true/false,           # Was data actually fetched?
    "version_created": true/false,        # Was new version created?
    "reason": "explanation"               # If no scrape: why not
}
```

## For Analysis Notebooks

Load versioned data:
```python
from scraper.version_manager import VersionManager

vm = VersionManager(data_dir="data")

# Load latest (automatically updated)
import json
with open("data/jugend_musiziert_data.json") as f:
    data = json.load(f)

# Or load specific version
data = vm.load_version_data("1706604000")

# See all versions
info = vm.get_version_info()
```

## Common Mistakes

❌ **Don't** do: `scrape()` > `scrape()` > `scrape()` repeatedly
- Creates duplicate versions
- Use smart mode which skips if no new data

✓ **Do** do: `scrape()` on schedule
- Runs daily, only creates version when new season detected
- Efficient and safe

❌ **Don't** do: `scrape(force=True)` daily
- Re-scrapes everything every time
- Wasteful

✓ **Do** do: `scrape(force=True, season_filter=[2024])` when needed
- Targeted re-scraping
- Only fetches what you need

## Typical Workflow

1. **First Run**
   ```python
   scraper.scrape()  # Scrapes all available seasons
   ```

2. **Daily Runs**
   ```python
   scraper.scrape()  # Only scrapes if new season detected
   ```

3. **If You Missed Data**
   ```python
   scraper.scrape(force=True, season_filter=[2024])  # Get missing season
   ```

4. **Regional Update**
   ```python
   scraper.scrape(force=True, region_filter=["Bayern"])  # Refresh one region
   ```

## Documentation

- **Full guide**: `scraper/VERSIONING.md`
- **Implementation**: `scraper/IMPLEMENTATION.md`
- **Examples**: `python scraper/examples_versioning.py`
- **Code**: `scraper/version_manager.py` and `scraper/scraper_versioned.py`

## Questions?

See `scraper/VERSIONING.md` for:
- Detailed decision logic
- More examples
- Best practices
- Integration patterns
