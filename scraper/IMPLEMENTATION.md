# Versioned Scraping System - Implementation Summary

## What's New

A complete **data versioning and smart scraping system** has been implemented to safely manage incremental tournament data updates.

## New Files Created

### Core Modules

1. **scraper/version_manager.py** (197 lines)
   - Manages version history and metadata
   - Detects new seasons/regions
   - Determines what should be scraped
   - Loads/saves versioned data

2. **scraper/scraper_versioned.py** (247 lines)
   - Wraps base scraper with version support
   - Implements smart scraping logic
   - Supports force re-scraping with filters
   - Main entry point for versioned scraping

3. **scraper/examples_versioning.py** (149 lines)
   - Usage examples and demonstrations
   - Typical workflow examples
   - Run: `python examples_versioning.py`

### Documentation

4. **scraper/VERSIONING.md** (350+ lines)
   - Complete version system documentation
   - Usage examples and decision logic
   - Best practices and workflows
   - Integration with analysis

### Configuration

5. **config.json** (updated)
   - Added `versioning` section
   - Controls default behavior
   - Season/region filtering options

### Data Structure

6. **data/versions/** (directory)
   - Stores individual version snapshots
   - Files: `v{timestamp}.json`

7. **data/versions.json** (auto-created)
   - Index of all versions
   - Metadata for each version
   - Season/region tracking

## How It Works

### Smart Scraping (Default)

```
User calls: scraper.scrape()
     ↓
Detect available seasons/regions from website
     ↓
Check: Have we scraped these before?
     ├─ New seasons/regions? → Scrape them ✓
     └─ All known? → Skip (no version created)
```

### Force Re-scraping

```
User calls: scraper.scrape(force=True, season_filter=[2025])
     ↓
Ignore history, scrape filtered seasons/regions
     ↓
Create version → Save data → Update main file
```

## Key Features

| Feature | Benefit |
|---------|---------|
| **Version IDs** | Unix timestamp (easy sorting, no conflicts) |
| **Smart Scraping** | Only new seasons by default (efficient) |
| **Force Mode** | Re-scrape with fine-grained control |
| **Filtering** | Limit re-scraping to seasons/regions |
| **Dry Run** | Preview before actual scraping |
| **History** | Complete version history with metadata |
| **Incremental** | Combine data from multiple versions |

## Usage Examples

### 1. Smart Scrape (Only New Data)
```python
from scraper.scraper_versioned import VersionedScraper

scraper = VersionedScraper(base_url="https://...", data_dir="data")
result = scraper.scrape()
```

### 2. Force Re-scrape Specific Season
```python
result = scraper.scrape(force=True, season_filter=[2025])
```

### 3. Force Re-scrape Specific Region
```python
result = scraper.scrape(force=True, region_filter=["Baden-Württemberg"])
```

### 4. Preview Before Scraping
```python
result = scraper.scrape(force=True, season_filter=[2025], dry_run=True)
```

### 5. Check Version History
```python
info = scraper.get_version_info()
print(f"Total versions: {info['total_versions']}")
print(f"Seasons: {info['scraped_seasons']}")
print(f"Regions: {info['scraped_regions']}")
```

## Data Organization

```
data/
├── jugend_musiziert_data.json      # Latest combined data
├── versions.json                    # Index of all versions
└── versions/
    ├── v1706604000.json            # Version 1
    ├── v1706690400.json            # Version 2
    └── v{timestamp}.json           # Current version
```

## Version Index Format

```json
{
  "versions": [
    {
      "version_id": "1706604000",
      "timestamp": "2024-01-30T12:00:00",
      "seasons": [2024, 2025],
      "regions": ["Baden-Württemberg"],
      "metadata": {"force": false},
      "data_file": "v1706604000.json"
    }
  ]
}
```

## Integration Points

### For Scraping
1. Import `VersionedScraper` instead of `JugendMusiziertScraper`
2. Call `scraper.scrape()` with optional parameters
3. Data automatically versioned and saved

### For Analysis
1. Use `VersionManager` to load specific versions
2. Or analyze latest data from `data/jugend_musiziert_data.json`
3. Version metadata available in `data/versions.json`

### For Configuration
Edit `config.json` `versioning` section:
- `enabled`: Turn on/off versioning
- `smart_scraping`: Enable smart mode (default)
- `force_scrape`: Default force mode (usually false)
- `season_filter`: Pre-filter seasons
- `region_filter`: Pre-filter regions

## Typical Workflows

### Scheduled Daily Scraping
```python
# Run daily - only scrapes on new seasons
scraper.scrape()
```

### Recovery from Errors
```python
# Re-scrape season if data was corrupted
scraper.scrape(force=True, season_filter=[2024])
```

### Region-Specific Updates
```python
# Update only one region
scraper.scrape(force=True, region_filter=["Bayern"])
```

### Complete Data Refresh
```python
# Re-scrape everything
scraper.scrape(force=True)
```

## Decision Tree

```
scraper.scrape(force=?, season_filter=?, region_filter=?, dry_run=?)
│
├─ dry_run=True?
│  └─ Show preview, don't scrape
│
├─ force=True?
│  ├─ season_filter provided?
│  │  └─ Scrape only filtered seasons
│  ├─ region_filter provided?
│  │  └─ Scrape only filtered regions
│  └─ Scrape all available data
│
└─ force=False? (Smart Mode)
   ├─ New seasons since last scrape?
   │  ├─ YES → Scrape new seasons
   │  └─ NO → Check regions
   ├─ New regions since last scrape?
   │  ├─ YES → Scrape new regions
   │  └─ NO → Skip (no version created)
   └─ If scraping: Create version, save data
```

## Next Steps

1. **Implement season/region detection** in `VersionedScraper.detect_seasons_and_regions()`
   - Parse website to find available seasons/regions
   - Return as list/set

2. **Update base scraper** to support season/region filtering
   - Modify `JugendMusiziertScraper` to accept season/region parameters
   - Return filtered data

3. **Test the workflow**
   - Run examples: `python scraper/examples_versioning.py`
   - Try: `scraper.scrape(dry_run=True)`

4. **Integrate with analysis**
   - Update notebook to use version manager
   - Load specific versions when needed

## Files Modified

- `config.json` - Added versioning configuration
- `README.md` - Added versioning feature and documentation link

## Files Created

- `scraper/version_manager.py` - Core versioning logic
- `scraper/scraper_versioned.py` - Versioned scraper wrapper
- `scraper/examples_versioning.py` - Usage examples
- `scraper/VERSIONING.md` - Complete documentation
- `data/versions/` - Storage for version snapshots
- This file - `IMPLEMENTATION.md`

## Architecture Benefits

1. **Safety**: No accidental re-scraping of known data
2. **Efficiency**: Only fetches new data by default
3. **Control**: Fine-grained re-scraping capabilities
4. **Traceability**: Complete history with timestamps
5. **Flexibility**: Support for both incremental and full updates
6. **Scalability**: Handles many seasons/regions efficiently
