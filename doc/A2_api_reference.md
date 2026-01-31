# A2. API Reference

Reference documentation for all public APIs in the jumu system.

## Scraper API

### JugendMusiziertScraper

Asynchronous scraper for fetching tournament data.

```python
from scraper.scraper_async import JugendMusiziertScraper

scraper = JugendMusiziertScraper()
data = await scraper.scrape()
```

**Methods**:

```python
async def fetch_seasons(session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
    """Fetch seasons data from API.
    
    Returns:
        Seasons data with structure:
        {
            'hydra:member': [season1, season2, ...],
            'hydra:totalItems': int,
            'hydra:view': {...}
        }
    """

async def fetch_timetable(
    session: aiohttp.ClientSession,
    season_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Fetch timetable entries (handles pagination automatically).
    
    Args:
        session: aiohttp session for connection pooling
        season_id: Optional filter by season
    
    Returns:
        Timetable data with entries and pagination metadata
    """

async def scrape() -> Dict[str, Any]:
    """Fetch all data in parallel.
    
    Returns:
        {'seasons': data, 'timetable': data}
    """

def save_data(data: Dict[str, Any], output_file: str = 'jugend_musiziert_data.json') -> None:
    """Save data to JSON file."""
```

## VersionManager API

Version tracking and smart scraping decisions.

```python
from scraper.version_manager import VersionManager

manager = VersionManager(data_dir=Path('data'))
```

**Methods**:

```python
def create_version(
    seasons: Set[int],
    regions: Set[str],
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Create and store a new version.
    
    Returns:
        Unix timestamp (version ID)
    """

def should_scrape(
    detected_seasons: Set[int],
    detected_regions: Set[str],
    force: bool = False,
    season_filter: Optional[List[int]] = None,
    region_filter: Optional[List[str]] = None
) -> bool:
    """Determine if scraping should proceed.
    
    Returns:
        True if scraping decision is YES
    """

def get_scraped_seasons() -> Set[int]:
    """Get all seasons previously scraped."""

def get_scraped_regions() -> Set[str]:
    """Get all regions previously scraped."""

def get_version_history() -> List[Dict[str, Any]]:
    """Get list of all versions with metadata."""
```

## DataProcessor API

Data transformation utilities.

```python
from analysis.data_processor import DataProcessor

processor = DataProcessor('data/jugend_musiziert_data.json')
seasons = processor.extract_seasons()
persons = processor.extract_persons()
```

**Methods**:

```python
def extract_seasons() -> List[Dict[str, Any]]:
    """Extract season data."""

def extract_persons() -> List[Dict[str, Any]]:
    """Extract person/participant data."""

def extract_instruments() -> List[Dict[str, Any]]:
    """Extract instrument data."""

def extract_timetables() -> List[Dict[str, Any]]:
    """Extract timetable/competition schedule data."""

def export_to_csv(data: List[Dict], filename: str) -> None:
    """Export data to CSV file."""
```

## Configuration

### pyproject.toml

```toml
[project]
requires-python = ">=3.8"
dependencies = [
    "aiohttp>=3.9.0",          # HTTP client (async)
    "polars>=0.19.0",          # Data analysis
    "jupyter>=1.0.0",
    "jupyterlab>=3.0.0",
    "ipykernel>=6.0.0",
]

[tool.mypy]
python_version = "3.14"        # Target version for type checking
```

### config.json

```json
{
    "versioning": {
        "enabled": true,
        "data_dir": "data",
        "smart_scraping": true,
        "force_scrape": false,
        "season_filter": null,
        "region_filter": null
    },
    "scraper": {
        "timeout": 10,
        "user_agent": "Mozilla/5.0..."
    }
}
```

## Environment Variables

None required. All configuration via config.json and CLI arguments.

## Error Handling

### Common Exceptions

```python
asyncio.TimeoutError          # Request timeout (10s)
aiohttp.ClientError           # Network error
json.JSONDecodeError          # Invalid JSON response
FileNotFoundError             # Missing data file
```

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Typical log output:
```
2026-01-31 14:23:45 - INFO - Fetching seasons from https://api.jugend-musiziert.org/api/seasons
2026-01-31 14:23:46 - INFO - Successfully fetched seasons data
2026-01-31 14:23:47 - INFO - Scraping timetable page 1: ...
```

## Performance

| Operation | Time | Memory |
|-----------|------|--------|
| Full scrape | <30s | <500MB |
| Version decision | <100ms | <10MB |
| Data normalization | <2s | varies by size |
| JSON save | <1s | <100MB |

## Rate Limits

- API timeout: 10 seconds per request
- Parallel requests: 2 concurrent (seasons + timetable)
- No throttling; uses connection pooling

