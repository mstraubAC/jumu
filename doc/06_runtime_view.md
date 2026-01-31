# 6. Runtime View

## 6.1 Scraping Sequence

```
User invokes: uv run scraper/scraper.py [--force] [--season-filter=...] [--region-filter=...]

1. VersionedScraper.__init__()
   ├─ Load version history from data/versions.json
   └─ Initialize JugendMusiziertScraper

2. VersionedScraper.scrape()
   ├─ IF dry_run: detect_seasons_and_regions(), print decision, exit
   ├─ ELSE: VersionManager.should_scrape(detected, force, filters)
   │  ├─ IF decision=SCRAPE: call JugendMusiziertScraper.scrape()
   │  │  ├─ fetch_seasons() [async, parallel]
   │  │  ├─ fetch_timetable() [async, parallel]
   │  │  └─ fetch_participants() [async, parallel]
   │  └─ Collect results in merged_data
   │
   ├─ Merge with existing data/jugend_musiziert_data.json
   ├─ Save merged → data/jugend_musiziert_data.json
   ├─ VersionManager.create_version(seasons, regions, metadata)
   │  ├─ Create snapshot: data/versions/v{timestamp}.json
   │  └─ Update index: data/versions.json
   └─ Return result summary

3. Output: {status, version_id, seasons_scraped, regions_scraped}
```

## 6.2 Analysis Sequence

```
User opens analysis.ipynb and executes cells

1. Load data
   └─ load_data() → raw JSON from data/jugend_musiziert_data.json

2. Inspect structure
   ├─ List top-level keys (seasons, timetables, etc.)
   └─ Count items in each category

3. Normalize to DataFrames
   ├─ extract_seasons() → DataFrame[season_id, year, ageGroups, ...]
   ├─ extract_timetables() → DataFrame[date, room_id, season_id, ...]
   ├─ extract_persons() → DataFrame[person_id, firstName, lastName, city, ...]
   ├─ extract_instruments() → DataFrame[instrument_id, name, family]
   ├─ extract_appearances() → DataFrame[appearance_id, person_id, instrument_id, ...]
   └─ extract_program_items() → DataFrame[title, opus, composer, duration, ...]

4. Ad-hoc queries
   └─ Use Polars filter/select to explore patterns
      ├─ Search for specific participants
      ├─ Aggregate by instrument
      ├─ Count appearances by season/region
      └─ Export to CSV for external analysis

5. Output: Summary statistics, visualizations
```

## 6.3 Concurrent Operations

### scraper.py Parallelization

```python
async def scrape(self):
    # Fetch all seasons concurrently
    seasons_data = await asyncio.gather(
        self.fetch_seasons(),
        self.fetch_timetable(),
        self.fetch_participants()
    )
    # All 3 requests happen in parallel via aiohttp connection pool
```

**Benefits**:
- 3 independent API calls: ~10s vs ~30s sequential
- aiohttp event loop manages concurrency transparently
- Connection pooling reuses HTTP connections

## 6.4 Error Handling

| Scenario | Handler | Recovery |
|----------|---------|----------|
| API timeout (>10s) | Log warning, skip season | Operator retries or forces re-scrape |
| Malformed JSON | Log error, skip block | Manual inspection of raw response |
| Network error | Log and re-raise | Operator retries or checks connectivity |
| Version conflict | Merge strategy (latest wins) | Snapshot preserves historical version |

