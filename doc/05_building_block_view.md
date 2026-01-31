# 5. Building Block View

## 5.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       CLI Entry Point                       │
│         scraper/scraper.py (async main function)            │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼────────┐  ┌────▼──────────────┐
│  JugendMusziert│  │ VersionedScraper  │
│    Scraper     │  │  (smart logic)    │
│                │  │                   │
│ - fetch_*()    │  │ - scrape()        │
│ - parse_*()    │  │ - should_scrape() │
│ - _get_json()  │  │ - detect_*()      │
└───────────────┘  └────┬───────────────┘
                         │
                   ┌─────▼──────────┐
                   │ VersionManager │
                   │                │
                   │ - create_*()   │
                   │ - get_scraped_*│
                   │ - decide()     │
                   └────┬───────────┘
                        │
        ┌───────────────┴────────────────┐
        │                                 │
   ┌────▼────────┐            ┌──────────▼──┐
   │ data/       │            │ data/       │
   │ jugend_...  │            │ versions/   │
   │ _data.json  │            │ v*.json     │
   └─────────────┘            └─────────────┘
```

## 5.2 scraper/ Directory

### scraper.py — Core Scraper
**Responsibility**: Fetch and parse data from Jugend musiziert API

**Dependencies**: aiohttp, json, logging

**Key Classes**:
- `JugendMusiziertScraper`: Main scraper with methods:
  - `async fetch_seasons()`: Fetch season list
  - `async fetch_timetable()`: Fetch competition schedule
  - `async fetch_participants()`: Fetch participant data
  - `async scrape()`: Orchestrate full scrape

**Interface**:
- Input: Season filter (optional), region filter (optional)
- Output: Dict with 'seasons', 'timetables', 'participants' keys

### scraper_versioned.py — Versioning Wrapper
**Responsibility**: Intelligent scraping with version detection

**Dependencies**: version_manager.py, scraper.py, json

**Key Classes**:
- `VersionedScraper`: Wrapper around JugendMusiziertScraper
  - `async scrape(force, season_filter, region_filter, dry_run)`: Main entry point
  - `async detect_seasons_and_regions()`: Parse available data
  - `async get_version_info()`: Return current version metadata

**Decision Logic**:
- IF force=True: Scrape everything
- ELIF season_filter: Scrape only matching seasons
- ELIF smart_scraping=True: Scrape only new seasons
- ELSE: Scrape all

### version_manager.py — Version Tracking
**Responsibility**: Track scraped data versions by timestamp

**Dependencies**: json, pathlib

**Key Classes**:
- `VersionManager`: Manage version history
  - `create_version(seasons, regions, metadata)`: Create new version entry
  - `should_scrape(detected_seasons, detected_regions, force, filters)`: Decision logic
  - `get_scraped_seasons()`: Return Set of previously scraped season IDs
  - `get_scraped_regions()`: Return Set of previously scraped regions

**Data Format**: 
- Version ID: Unix timestamp (seconds)
- Stored at: `data/versions.json` (index) and `data/versions/v{id}.json` (snapshot)

## 5.3 analysis/ Directory

### data_processor.py — Data Utilities
**Responsibility**: Transform JSON to normalized Polars DataFrames

**Dependencies**: polars, json, pathlib

**Key Functions**:
- `load_data()`: Load JSON from `data/jugend_musiziert_data.json`
- `extract_seasons()`: Return seasons DataFrame
- `extract_timetables()`: Return timetables DataFrame
- `extract_persons()`: Return persons DataFrame
- Normalization functions for each entity

### analysis.ipynb — Interactive Analysis
**Responsibility**: Exploratory data analysis and visualization

**Usage**: Jupyter notebook for ad-hoc analysis, pattern discovery

## 5.4 data/ Directory

**Structure**:
```
data/
├── jugend_musiziert_data.json    # Master dataset (current)
├── versions.json                 # Version index
└── versions/
    ├── v1706745600.json          # Version snapshot
    ├── v1706832000.json
    └── ...
```

**Access Pattern**:
- Always read from `jugend_musiziert_data.json` for current analysis
- Version snapshots used for historical comparison and re-scrape decisions

