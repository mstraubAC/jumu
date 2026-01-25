# Quick Start Guide

## Installation

### 1. Install uv

```bash
pip install uv
# Or visit: https://docs.astral.sh/uv/getting-started/
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the Basic Scraper

```bash
uv run python scraper/scraper.py
```

Expected output:
```
============================================================
Jugend musiziert Tournament Scraper
============================================================

[Step 1] Discovering API endpoints...
...
[Step 2] Extracting embedded JSON data...
...
[Step 3] Saving data...

============================================================
SCRAPING SUMMARY
============================================================
✓ Discovered API endpoints: X
✓ Embedded data blocks found: Y
✓ Data saved to: jugend_musiziert_data.json
```

## What You Get

After running the scraper, you'll have a file called `jugend_musiziert_data.json` containing:

- **API Endpoints**: URLs to JSON APIs used by the website
- **Embedded Data**: JSON data injected directly into the page
- **Metadata**: Information about what was scraped

## Analyzing the Data

### View the Raw Data

```bash
# Pretty print the JSON
python3 -c "import json; print(json.dumps(json.load(open('jugend_musiziert_data.json')), indent=2))" | head -100
```

### Extract Specific Information

```bash
# Count embedded data blocks
python3 -c "import json; data = json.load(open('jugend_musiziert_data.json')); print(f'Found {len(data[\"embedded_data\"])} data blocks')"
```

### Use the Data Processor

```bash
# View summary
uv run python analysis/data_processor.py analysis/jugend_musiziert_data.json --summary

# Export to CSV (if participant data is structured)
uv run python analysis/data_processor.py analysis/jugend_musiziert_data.json --csv participants.csv
```

## Advanced Usage

### Run the Selenium Scraper (if JavaScript rendering needed)

```bash
# Install Selenium dependencies
uv sync --extra selenium

# Download ChromeDriver: https://chromedriver.chromium.org/
# Place it in your PATH or current directory

# Run the scraper
uv run python scraper/scraper_selenium.py
```

### Schedule Regular Scraping

```bash
# Install APScheduler via uv
uv pip install APScheduler

# Create a scheduled task:
```

```python
# scheduled_scraper.py
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.scraper import JugendMusiziertScraper
import atexit

def job():
    scraper = JugendMusiziertScraper("https://...")
    data = scraper.scrape_schedule()
    scraper.save_data(data)

scheduler = BackgroundScheduler()
scheduler.add_job(func=job, trigger="cron", hour=9, minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())
```

## Troubleshooting

### No data found?

1. **Check the URL**: Make sure the URL is correct and accessible
   ```bash
   curl -I "https://www.jugend-musiziert.org/..." | grep -i "200\|301\|302"
   ```

2. **Check page structure**: The website might have changed
   ```bash
   curl "https://www.jugend-musiziert.org/..." | grep -i "participant\|api\|json" | head -5
   ```

3. **Try the Selenium scraper**: JavaScript might be required to load data
   ```bash
   uv run python scraper/scraper_selenium.py
   ```

### Dependencies not installed?

```bash
# Ensure all dependencies are installed via uv
uv sync

# Verify installation
uv run python -c "import requests; import json; print('OK')"
```

## File Structure

```
/Users/marcel/projects/jumu/
├── scraper/
│   ├── scraper.py                 # Main scraper (HTTP + regex)
│   ├── scraper_selenium.py        # Advanced scraper (JavaScript rendering)
│   └── SCRAPER_CORRECTION.md
├── analysis/
│   ├── data_processor.py          # Data analysis and export
│   ├── examples.py                # Usage examples
│   └── jugend_musiziert_data.json # Output from scraper.py
├── config.json                    # Configuration file
├── pyproject.toml                 # Project config
├── README.md                      # Full documentation
└── QUICKSTART.md                  # This file
```

## Common Tasks

### Extract participant names
```bash
python3 << 'EOF'
import json

data = json.load(open('jugend_musiziert_data.json'))
for block in data.get('embedded_data', []):
    block_data = block.get('data', {})
    
    # Look for participant-like structures
    for key, value in block_data.items():
        if isinstance(value, dict) and any(k in str(value).lower() for k in ['name', 'participant', 'person']):
            print(f"Found in key '{key}':")
            print(json.dumps(value, indent=2, ensure_ascii=False)[:200])
            break
EOF
```

### Filter by age group
```bash
python data_processor.py jugend_musiziert_data.json --age-group "III" --csv group_III.csv
```

### Compare two scrapes
```bash
diff <(jq '.' jugend_musiziert_data.json | sort) \
     <(jq '.' jugend_musiziert_data_old.json | sort)
```

## Next Steps

1. ✅ Successfully ran the scraper
2. ✅ Extracted participant data
3. 🔄 Analyze and filter the data using `data_processor.py`
4. 📊 Export to CSV/Excel for further analysis
5. 📅 Schedule regular scrapes to monitor changes
6. 🔗 Integrate with your own application

## Additional Resources

- [Requests Documentation](https://docs.python-requests.org/)
- [BeautifulSoup Tutorial](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selenium Python](https://selenium-python.readthedocs.io/)
- [JSON in Python](https://docs.python.org/3/library/json.html)

## Questions?

- Check the logs: All operations are logged in detail
- Examine output JSON: Use `jq` or a JSON viewer to explore structure
- Review the code: Both scrapers have extensive comments
- Check `config.json`: Adjust settings as needed

Enjoy your tournament data! 🎵
