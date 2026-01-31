# 8. Crosscutting Concepts

## 8.1 Coding Standards

### Type Hints (Mandatory)
```python
from typing import Optional, List, Dict, Any

# Good
async def fetch_seasons(self) -> Dict[str, Any]:
    pass

def extract_persons(data: Dict[str, Any]) -> pl.DataFrame:
    pass

# Bad (no type hints)
async def fetch_seasons(self):
    pass
```

### Docstrings (One-line + Detailed)
```python
def should_scrape(self, detected_seasons: Set[int], force: bool) -> bool:
    """Determine if scraping should proceed.
    
    Args:
        detected_seasons: Set of season IDs available on website.
        force: If True, always scrape regardless of history.
    
    Returns:
        True if scraping should proceed, False otherwise.
    
    Logic:
        - If force=True: always True
        - If smart_scraping=False: always True
        - Otherwise: True if detected_seasons > previously_scraped_seasons
    """
    pass
```

### Async/Await (I/O-bound operations)
```python
# Good: Concurrent API calls
async def scrape(self) -> Dict[str, Any]:
    seasons, timetable = await asyncio.gather(
        self.fetch_seasons(),
        self.fetch_timetable()
    )
    return {**seasons, **timetable}

# Bad: Sequential (slow)
async def scrape(self) -> Dict[str, Any]:
    seasons = await self.fetch_seasons()
    timetable = await self.fetch_timetable()
    return {**seasons, **timetable}
```

## 8.2 Data Structure Normalization

### Entity-Relationship Model

```
Seasons (1) ─── (many) SeasonAgeGroups
                              │
                              ├─ (many) Contests
                              └─ (many) Timetables
                                          │
                                          ├─ (many) Appointments
                                          │             │
                                          │             └─ (many) Entries
                                          │                         │
                                          │                         ├─ ProgramItems
                                          │                         │   └─ Contributors
                                          │                         │
                                          │                         └─ Appearances
                                          │                             └─ Persons
                                          │                             └─ Instruments
                                          │
                                          └─ Rooms
                                              └─ Venues

Foreign Key Relationships:
- Timetable.room_id → Rooms.room_id
- Appointment.timetable_group_id → TimetableGroups.timetable_group_id
- Appearance.person_id → Persons.person_id
- Appearance.instrument_id → Instruments.instrument_id
```

### Normalization Rules

1. **Seasons**: Never duplicate season IDs. Use year/number as identifier.
2. **Persons**: Deduplicate by firstName+lastName+city. One person can have many appearances.
3. **Instruments**: Deduplicate by name. Reuse across appearances.
4. **Program Items**: Keep contributors as nested JSON (no separate table).
5. **Appearances**: Link person → instrument in specific entry context.

## 8.3 Logging and Monitoring

### Log Levels
```python
logger.debug("Fetching %d seasons", len(season_ids))        # Development
logger.info("Successfully scraped 28 seasons")              # Operations
logger.warning("API returned 429, retrying...")             # Issues
logger.error("Failed to parse JSON: %s", str(e))            # Failures
```

### Log Output
```
2026-01-31 14:23:45 - INFO - Fetching seasons from https://api.jugend-musiziert.org/api/seasons
2026-01-31 14:23:46 - INFO - Successfully fetched seasons data (28 items)
2026-01-31 14:23:47 - INFO - Scraping timetable for season 2025...
2026-01-31 14:25:02 - INFO - Scraping complete. Version: 1706775000
```

## 8.4 Version Management Strategy

### Version Metadata
```json
{
  "version_id": 1706775000,
  "timestamp": "2026-01-31T14:23:00Z",
  "seasons": [2023, 2024, 2025],
  "regions": ["Bayern", "Hessen", "..."],
  "item_counts": {
    "seasons": 28,
    "timetables": 1247,
    "participants": 3891
  },
  "md5_hash": "abc123..."
}
```

### Versioning Decision Tree
```
User runs: uv run scraper/scraper.py [options]

├─ --help → show usage
├─ --dry-run → detect_seasons_and_regions(), print decision, exit
├─ --force → delete old version, scrape all
├─ --season-filter=2024,2025 → scrape only those seasons
├─ --region-filter=Bayern → scrape only that region
└─ [default] → smart scrape (only new seasons)
```

