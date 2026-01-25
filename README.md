# Jugend musiziert Tournament Scraper

A Python web scraper for extracting participant data from the Jugend musiziert (a major music competition in Germany) tournament schedule and participant list.

## Overview

This project provides tools to scrape participant information from the Jugend musiziert regional tournament website. The website uses a web API to serve JSON data containing participant details, schedule information, and competition categories.

**Target URL**: https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan

## Features

- **API Endpoint Discovery**: Automatically finds and extracts API endpoints from the webpage
- **Embedded JSON Extraction**: Extracts JSON data embedded in script tags and window objects
- **Multiple Scraping Strategies**: Different approaches for static content and JavaScript-rendered pages
- **Data Persistence**: Saves extracted data to JSON files for further processing
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Files

- **scraper.py**: Main scraper using requests and HTML parsing
  - Discovers API endpoints from the page
  - Extracts embedded JSON data from script tags
  - Works with static HTML and inline JSON
  - No JavaScript rendering needed

- **scraper_selenium.py**: Advanced scraper using Selenium
  - Renders pages with JavaScript
  - Captures dynamically loaded content
  - Monitors window object for injected data
  - Requires Chrome/Chromium and ChromeDriver

- **requirements.txt**: Python dependencies
- **README.md**: This file

## Installation

### Using uv (Recommended)

```bash
# Install uv
pip install uv

# Clone or navigate to the project directory
cd /Users/marcel/projects/jumu

# Install dependencies with uv
uv sync
```

### Basic Setup with pip (alternative)

```bash
cd /Users/marcel/projects/jumu
pip install -r requirements.txt
```

### Advanced Setup (for Selenium scraper)

Using uv:
```bash
# Install with Selenium support
uv sync --extra selenium

# Download ChromeDriver: https://chromedriver.chromium.org/
```

Using pip:
```bash
pip install selenium
# Download ChromeDriver: https://chromedriver.chromium.org/
```

## Usage

### With uv

```bash
# Install dependencies
uv sync

# Run basic scraper
uv run python scraper.py

# Process data
uv run python data_processor.py jugend_musiziert_data.json

# Run examples
uv run python examples.py
```

### With pip (after installing dependencies)

```bash
python scraper.py
python data_processor.py jugend_musiziert_data.json
python examples.py
```

### Basic Scraper

Using uv:
```bash
uv run python scraper.py
```

Or directly:
```bash
python scraper.py
```

This will:
1. Fetch the tournament page
2. Discover API endpoints embedded in the HTML
3. Extract JSON data from script tags
4. Save all collected data to `jugend_musiziert_data.json`

### Advanced Scraper (Selenium)

Using uv:
```bash
uv sync --extra selenium
uv run python scraper_selenium.py
```

Or directly:
```bash
python scraper_selenium.py
```

This will:
1. Open a Chrome browser and load the page
2. Wait for JavaScript to execute
3. Extract all JSON data from the rendered page
4. Save collected data to `jugend_musiziert_selenium.json`

## Output Format

Both scrapers produce JSON files with the following structure:

```json
{
  "url": "https://www.jugend-musiziert.org/...",
  "endpoints_discovered": [
    "/api/schedule",
    "/api/participants",
    ...
  ],
  "embedded_data": [
    {
      "source": "script_data_VARIABLE_NAME",
      "data": { ... }
    }
  ],
  "metadata": {
    "total_endpoints": 5,
    "total_data_blocks": 3
  }
}
```

## Data Structure

The extracted data typically contains:

- **Participant Information**
  - Name
  - Location/City
  - Instrument
  - Age Group

- **Schedule Information**
  - Date and Time
  - Venue/Location
  - Category/Genre
  - Program Details (compositions, duration)

- **Competition Details**
  - Categories (e.g., "Drum-Set (Pop)", "Akkordeon-Kammermusik")
  - Age Groups (Ia, Ib, II, III, IV, V, VI)
  - Judges and Locations

## API Patterns

The website uses several API patterns:

1. **RESTful APIs**: `/api/schedule`, `/api/participants`
2. **Embedded JSON**: Data injected in window variables
3. **Script Tags**: JSON data in `<script type="application/json">` tags

## Customization

### Modify Target URL

Edit the `url` variable in the `main()` function:

```python
url = "https://your-target-url.com"
```

### Filter Specific Data

Extend the scrapers to filter specific categories or age groups:

```python
def filter_participants(data, category=None, age_group=None):
    # Custom filtering logic
    pass
```

### Export Formats

Modify the output format (currently JSON) to:
- CSV: Use `csv` module
- Excel: Use `openpyxl` or `pandas`
- Database: Use `sqlite3` or `sqlalchemy`

## Troubleshooting

### "No data collected" error

1. Check if the URL is correct and accessible
2. The page structure may have changed - update regex patterns
3. The API might require authentication or specific headers

### Selenium driver issues

- Ensure ChromeDriver version matches your Chrome version
- Check that Chrome/Chromium is installed
- Verify ChromeDriver is in your PATH

### JSON parsing errors

- Some embedded JSON might be minified or have special characters
- The regex patterns may need adjustment for the specific page structure

## Advanced Usage

### Combining both scrapers

```python
from scraper import JugendMusiziertScraper
from scraper_selenium import SeleniumScraper

# Try static approach first (faster)
static_scraper = JugendMusiziertScraper(url)
static_data = static_scraper.scrape_schedule()

# If insufficient, use Selenium (slower but more thorough)
if not static_data:
    selenium_scraper = SeleniumScraper(url)
    selenium_data = selenium_scraper.scrape()
```

### Monitoring for changes

Run the scraper periodically and compare outputs:

```bash
# Compare new data with previous run
diff <(jq '.embedded_data | length' jugend_musiziert_data.json) \
     <(jq '.embedded_data | length' jugend_musiziert_data_old.json)
```

## Performance Notes

- **Basic Scraper**: ~1-5 seconds (network dependent)
- **Selenium Scraper**: ~10-30 seconds (includes browser startup and JavaScript execution)

## Ethical Considerations

- Always check the website's `robots.txt` and terms of service
- Respect rate limiting - add delays between requests if scraping multiple pages
- Consider contacting the website administrator for bulk data access
- Use the data responsibly and respect privacy

## Future Enhancements

- [ ] Implement caching to avoid redundant requests
- [ ] Add database storage (SQLite, PostgreSQL)
- [ ] Create a scheduled scraper (APScheduler)
- [ ] Build a web dashboard to visualize participant data
- [ ] Add export to CSV/Excel formats
- [ ] Implement error recovery and retry logic
- [ ] Create unit tests for scraper components

## License

This project is provided as-is for educational purposes.

## Contact

For questions or improvements, modify the scripts as needed for your use case.
