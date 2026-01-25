# API Reference & Technical Details

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         Jugend musiziert Scraper Architecture            │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐
│  scraper.py      │ ← Fast, HTTP-based
│  (HTTP + Regex)  │   No JS execution needed
└────────┬─────────┘
         │
         ├─→ API Endpoint Discovery
         ├─→ HTML Parsing
         ├─→ JSON Extraction
         └─→ Data Aggregation
              │
              ↓
    ┌─────────────────────┐
    │ jugend_musiziert_   │
    │ data.json           │
    └────────┬────────────┘
             │
    ┌────────▼──────────┐
    │ data_processor.py │ ← Analysis & Export
    │ (Pandas-ready)    │
    └────────┬──────────┘
             │
             ├─→ Extraction
             ├─→ Filtering
             ├─→ Grouping
             └─→ CSV Export
                  │
                  ↓
        ┌──────────────────┐
        │ participants.csv │
        └──────────────────┘

    (Alternative)
┌──────────────────────────┐
│ scraper_selenium.py      │ ← Slow, JS-enabled
│ (Selenium + Chrome)      │   Full page render
└────────┬─────────────────┘
         │
         ├─→ Browser Init
         ├─→ Page Load
         ├─→ JS Execution
         ├─→ DOM Parsing
         └─→ Window Object Inspection
              │
              ↓
    jugend_musiziert_selenium.json
```

## Class Reference

### JugendMusiziertScraper

```python
class JugendMusiziertScraper:
    """Main scraper for Jugend musiziert tournament data"""
    
    def __init__(self, base_url: str)
        # Initialize with tournament URL
    
    def _extract_api_base(self) -> str
        # Extract base API URL from page
    
    def _find_api_endpoints(self) -> List[str]
        # Discover API endpoints in HTML
    
    def fetch_json_from_api(self, endpoint: str) -> Optional[Dict]
        # Fetch JSON from discovered endpoint
    
    def scrape_schedule(self) -> List[Dict[str, Any]]
        # Extract embedded JSON from page
    
    def save_data(self, data: List[Dict], output_file: str)
        # Save collected data to JSON file
```

**Attributes**:
- `base_url`: Target tournament URL
- `session`: Requests session object
- `api_base`: Discovered API base URL
- `discovered_endpoints`: List of found API endpoints

### DataProcessor

```python
class DataProcessor:
    """Process and analyze scraped data"""
    
    def __init__(self, json_file: str)
        # Load data from JSON file
    
    def extract_participants(self) -> List[Dict]
        # Extract participant records
    
    def filter_by_category(self, participants, category) -> List[Dict]
        # Filter by competition category
    
    def filter_by_age_group(self, participants, age_group) -> List[Dict]
        # Filter by age group
    
    def group_by_category(self, participants) -> Dict
        # Group participants by category
    
    def export_to_csv(self, participants, output_file)
        # Export to CSV format
    
    def print_summary(self)
        # Print data summary
```

## API Endpoint Patterns

### Discovered Endpoints

Common API patterns detected:

```
/api/schedule
/api/participants
/api/categories
/api/locations
/api/judges
/api/results
```

### JSON Data Injection

Common data injection patterns:

```javascript
window.__NEXT_DATA__ = {...}
window.__data = {...}
window.__state = {...}
var scheduleData = {...}
var participantList = {...}
```

### Script Tags

```html
<script type="application/json" id="__NEXT_DATA__">
  {...}
</script>
```

## Data Structures

### Schedule Entry

```json
{
  "date": "2026-01-31",
  "time": "16:00",
  "category": "Akkordeon-Kammermusik",
  "ageGroup": "V",
  "location": "Rudolf Steiner Schule Nürtingen",
  "hall": "Rotes Haus | Kleiner Saal",
  "participants": [...],
  "program": [...]
}
```

### Participant Entry

```json
{
  "name": "Patrick Meier",
  "instrument": "Akkordeon",
  "location": "Mühlacker",
  "ageGroup": "V",
  "ensemble": "Patrick Meier, Akkordeon - Nicola Witzmann, Violine",
  "program": [
    {
      "composer": "Johann Sebastian Bach",
      "title": "Sonata Nr. 6 für Violine und Cembalo G-Dur",
      "duration": "3′20"
    }
  ]
}
```

### Program Entry

```json
{
  "composer": "Johann Sebastian Bach",
  "birthYear": 1685,
  "deathYear": 1750,
  "title": "Sonata Nr. 6 für Violine und Cembalo G-Dur",
  "catalogueNumber": "BWV 1019",
  "movements": [
    {
      "number": 1,
      "name": "Allegro",
      "duration": "3′20"
    }
  ]
}
```

## HTTP Request Headers

Default headers used by scraper:

```python
{
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

## Error Handling

### Exception Hierarchy

```python
requests.exceptions.RequestException
├── ConnectionError
├── HTTPError
├── URLRequired
├── TooManyRedirects
└── Timeout

json.JSONDecodeError
    └── ValueError (invalid JSON)
```

### Recovery Strategies

1. **Network Errors**: Retry with exponential backoff
2. **JSON Errors**: Fall back to text parsing
3. **Timeout**: Increase timeout and retry
4. **SSL Errors**: Verify SSL certificates

## Regex Patterns

### API Endpoint Pattern

```regex
(?:fetch|XMLHttpRequest|api)\s*\(\s*['"`]([^'"`]*(?:api|json|data)[^'"`]*)['""`]
```

### JSON Injection Pattern

```regex
window\.__(\w+)\s*=\s*({.*?});
```

### Script Tag Pattern

```regex
<script[^>]*type=['"]application/json['"][^>]*>(.*?)</script>
```

## Configuration Options

### scraper.py Settings

```python
request_timeout = 10           # Request timeout in seconds
user_agent = "Mozilla/5.0..."  # Custom user agent
verify_ssl = True              # Verify SSL certificates
```

### scraper_selenium.py Settings

```python
headless = False               # Run browser headless
wait_time = 5                  # Wait for JS execution (seconds)
disable_sandbox = True         # Disable Chrome sandbox
disable_dev_shm = True         # Disable /dev/shm usage
```

## Performance Optimization

### Caching

```python
import functools
import pickle

@functools.lru_cache(maxsize=128)
def cached_api_call(endpoint: str):
    return fetch_json_from_api(endpoint)
```

### Parallel Requests

```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_from_endpoint, ep) for ep in endpoints]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

### Database Integration

```python
import sqlite3

conn = sqlite3.connect('tournament.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE participants (
        id INTEGER PRIMARY KEY,
        name TEXT,
        instrument TEXT,
        location TEXT,
        age_group TEXT,
        category TEXT
    )
''')

cursor.execute(
    'INSERT INTO participants VALUES (?,?,?,?,?,?)',
    (id, name, instrument, location, age_group, category)
)
conn.commit()
```

## Logging Configuration

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
```

### Log Levels

```
DEBUG   - Detailed diagnostic info
INFO    - General informational messages
WARNING - Warning messages for issues
ERROR   - Error messages for failures
CRITICAL- Critical errors requiring action
```

## Testing

### Unit Test Template

```python
import unittest
from scraper import JugendMusiziertScraper

class TestScraper(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com/tournament"
        self.scraper = JugendMusiziertScraper(self.url)
    
    def test_api_discovery(self):
        endpoints = self.scraper._find_api_endpoints()
        self.assertIsInstance(endpoints, list)
    
    def test_data_extraction(self):
        data = self.scraper.scrape_schedule()
        self.assertGreater(len(data), 0)
```

## Troubleshooting Guide

### Debug Commands

```bash
# Check HTTP connectivity
curl -v https://www.jugend-musiziert.org/

# Extract all script tags
curl -s https://... | grep -o '<script.*</script>' | head -1

# Validate JSON output
python -m json.tool jugend_musiziert_data.json | head -20

# Check for specific data
jq '.embedded_data[].source' jugend_musiziert_data.json
```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Timeout | Slow network | Increase timeout in config |
| JSON error | Invalid JSON | Check API response |
| No endpoints | Page changed | Update regex patterns |
| Selenium error | Driver issue | Verify ChromeDriver path |
| Permission denied | File write | Check directory permissions |

---

**Last Updated**: January 2026
**Version**: 1.0
