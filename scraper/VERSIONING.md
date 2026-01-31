# Versioned Scraping System

## Overview

The versioning system enables **safe, incremental scraping** of tournament data. Key features:

- **Smart Scraping**: Only scrapes new seasons/regions by default
- **Version Control**: Every scrape creates a timestamped version
- **Selective Re-scraping**: Force mode to re-scrape specific seasons/regions
- **Data Integrity**: Maintains complete history of all versions

## Architecture

```
data/
├── jugend_musiziert_data.json     # Latest data (always current)
├── versions.json                   # Version index and history
└── versions/
    ├── v1706604000.json           # Version 1 (Jan 30, 2024)
    ├── v1706690400.json           # Version 2 (Jan 31, 2024)
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

## Usage

### 1. Smart Scraping (Default)

Only scrapes new seasons:

```python
from scraper.scraper_versioned import VersionedScraper

scraper = VersionedScraper(
    base_url="https://...",
    data_dir="data"
)

# Only scrapes new seasons
result = scraper.scrape()
```

**Output:**
- If no new seasons: "No new seasons or regions detected"
- If new seasons found: Creates version, saves data

### 2. Force Re-scrape All

Re-scrape all available data:

```python
result = scraper.scrape(force=True)
```

### 3. Re-scrape Specific Season

Force re-scrape only a particular season:

```python
result = scraper.scrape(force=True, season_filter=[2025])
```

### 4. Re-scrape Specific Region

Force re-scrape only a particular region:

```python
result = scraper.scrape(force=True, region_filter=["Baden-Württemberg"])
```

### 5. Combine Filters

Re-scrape specific season AND region:

```python
result = scraper.scrape(
    force=True,
    season_filter=[2025],
    region_filter=["Baden-Württemberg"]
)
```

### 6. Dry Run

Preview what would be scraped without actually scraping:

```python
result = scraper.scrape(force=True, season_filter=[2025], dry_run=True)
```

## Decision Logic

The `should_scrape()` method determines what to scrape:

### Smart Mode (Default)

```
Are there NEW seasons/regions?
  ├─ YES: Scrape them → Create version
  └─ NO:  Skip → "No new data detected"
```

### Force Mode

```
force=True?
  ├─ YES: Scrape everything (or filters if provided) → Create version
  └─ NO:  Apply smart mode logic
```

### With Filters

```
season_filter=[2025]?
  ├─ Include: Only scrape season 2025
  └─ Skip: Scrape all seasons

region_filter=["BW"]?
  ├─ Include: Only scrape region BW
  └─ Skip: Scrape all regions
```

## Version Manager API

```python
from scraper.version_manager import VersionManager

vm = VersionManager(data_dir="data")

# Get all version info
info = vm.get_version_info()

# Get scraped seasons and regions
seasons = vm.get_scraped_seasons()  # Set of season IDs
regions = vm.get_scraped_regions()  # Set of region identifiers

# Load a specific version
data = vm.load_version_data(version_id="1706604000")

# Check what should be scraped
decision = vm.should_scrape(
    detected_seasons=[2024, 2025],
    detected_regions=["Baden-Württemberg", "Bayern"],
    force=False,
    season_filter=None,
    region_filter=None
)
```

## Configuration

Update `config.json` to control versioning behavior:

```json
{
  "versioning": {
    "enabled": true,
    "data_dir": "data",
    "smart_scraping": true,
    "force_scrape": false,
    "season_filter": null,
    "region_filter": null
  }
}
```

## Workflow Examples

### Scenario 1: Regular Scheduled Scraping

```python
# Run daily
scraper.scrape()  # Smart mode - only new data
```

**Behavior:**
- Day 1: Detects season 2025 → Creates v1, saves data
- Day 2-7: No new seasons → Skips
- Day 8: Season 2026 detected → Creates v2, saves data

### Scenario 2: Missing a Specific Season

```python
# Re-scrape season 2024
scraper.scrape(force=True, season_filter=[2024])
```

**Behavior:**
- Creates new version with only season 2024
- Updates `jugend_musiziert_data.json`

### Scenario 3: Region-Specific Update

```python
# Only update Baden-Württemberg data
scraper.scrape(force=True, region_filter=["Baden-Württemberg"])
```

### Scenario 4: Complete Refresh

```python
# Re-scrape everything
scraper.scrape(force=True)
```

## Data Files

### Latest Data
`data/jugend_musiziert_data.json` - Always contains the most recent combined data. Used by analysis notebooks.

### Version Index
`data/versions.json` - Tracks all versions and metadata:

```json
{
  "versions": [
    {
      "version_id": "1706604000",
      "timestamp": "2024-01-30T12:00:00",
      "seasons": [2024],
      "regions": ["Baden-Württemberg"],
      "metadata": {},
      "data_file": "v1706604000.json"
    }
  ]
}
```

### Version Data
`data/versions/v{timestamp}.json` - Individual version snapshots.

## Integration with Analysis

Update your analysis notebook to use versioned data:

```python
# Load latest version automatically
from scraper.version_manager import VersionManager

vm = VersionManager(data_dir="data")
version_info = vm.get_version_info()
print(f"Analyzing version {version_info['latest_version']['version_id']}")

# Or load specific version
data = vm.load_version_data(version_id="1706604000")
```

## Best Practices

1. **Run smart scraping regularly** (daily/weekly)
   ```python
   scraper.scrape()  # Only updates on new seasons
   ```

2. **Use force + filters for targeted updates**
   ```python
   scraper.scrape(force=True, season_filter=[2025])
   ```

3. **Dry run before force scraping**
   ```python
   scraper.scrape(force=True, season_filter=[2025], dry_run=True)
   ```

4. **Check version history**
   ```python
   info = scraper.get_version_info()
   print(f"Total versions: {info['total_versions']}")
   print(f"Seasons: {info['scraped_seasons']}")
   print(f"Regions: {info['scraped_regions']}")
   ```

5. **Analyze version-specific data when needed**
   ```python
   # Load v1 instead of latest
   data = scraper.get_version_data("1706604000")
   ```
