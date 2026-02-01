# Jugend musiziert Data Scraper & Analysis

A modern Python platform for extracting and analyzing participant data from the Jugend musiziert regional tournament website.

## Quick Start

See [GETTING_STARTED.md](GETTING_STARTED.md) for a 5-minute setup guide.

## Project Overview

**jumu** is a data scraping and analysis platform for the Jugend musiziert (German youth music competition) dataset. It extracts structured tournament data from the official website and provides tools for comprehensive analysis of participation patterns, competition results, and musical repertoire across multiple seasons and age groups.

## Key Features

- **Smart Versioning**: Incremental scraping with automatic season/region detection
- **Async Parallelization**: Concurrent HTTP requests using `aiohttp` for fast data acquisition
- **Structured Output**: JSON format with normalized data ready for analysis
- **Polars-Based Analysis**: Modern data analysis using Polars (not pandas) for performance and clarity
- **CLI-First Design**: Command-line interface for all operations

## Project Structure

```
jumu/
├── README.md                        # Project overview
├── GETTING_STARTED.md               # Setup and first-run instructions
├── pyproject.toml                   # Project metadata
├── config.json                      # Configuration
├── requirements.txt                 # Python dependencies
├── scraper/
│   ├── scraper.py                   # CLI entry point
│   ├── src/
│   │   ├── scraper.py               # Main synchronous scraper
│   │   ├── scraper_async.py         # Async scraper (aiohttp)
│   │   ├── scraper_selenium.py      # Selenium-based scraper
│   │   └── version_manager.py       # Version tracking
│   └── test/                        # Scraper tests
├── analysis/
│   ├── analysis.ipynb               # Exploratory data analysis
│   ├── src/
│   │   └── data_processor.py        # Data transformation utilities
│   └── test/                        # Analysis tests
├── data/
│   ├── jugend_musiziert_data.json   # Scraped data
│   └── versions/                    # Version history
└── doc/                             # ARC42 architecture documentation
    ├── 01_introduction_and_goals.md
    ├── ... (sections 2-11)
    └── A2_api_reference.md
```

## Installation

```bash
# 1. Install uv (Python package manager)
pip install uv

# 2. Install dependencies
uv sync

# 3. Verify installation
uv run scraper/scraper.py --help
```

## Basic Usage

```bash
# Run scraper (creates data/ directory, uses smart versioning)
uv run scraper/scraper.py

# Preview without scraping (dry-run)
uv run scraper/scraper.py --dry-run

# Force full re-scrape
uv run scraper/scraper.py --force

# Scrape specific season(s)
uv run scraper/scraper.py --season-filter=2024,2025

# Explore data in analysis notebook
jupyter lab analysis/analysis.ipynb
```

## Architecture Highlights

The project follows **ARC42 architecture documentation** with:

- **Separation of Concerns**: Scraping, data organization, and analysis in distinct modules
- **Version History**: Complete tracking of all scraped data with Unix timestamps
- **Async Parallelization**: Concurrent requests for improved performance
- **Modern Python**: Type hints, async/await, Python 3.14 compatibility
- **Polars for Analysis**: Efficient data transformation and analysis

See [doc/](doc/) for complete architecture documentation.

## Next Steps

1. **Getting Started**: Follow [GETTING_STARTED.md](GETTING_STARTED.md) for setup
2. **Architecture**: Read [doc/01_introduction_and_goals.md](doc/01_introduction_and_goals.md)
3. **API Reference**: Check [doc/A2_api_reference.md](doc/A2_api_reference.md)

## License

Educational and research use.
