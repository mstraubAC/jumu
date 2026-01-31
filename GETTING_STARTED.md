# Getting Started

## Installation (5 minutes)

### Prerequisites
- Python 3.8+ (uv will download 3.14 if needed)
- Git

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd jumu

# 2. Install Python 3.14 (if not available)
uv python install 3.14

# 3. Install project dependencies
uv sync

# 4. Verify installation
uv run scraper/scraper.py --help
```

## First Run: Scrape Data

```bash
# Run scraper (creates data/ directory automatically)
uv run scraper/scraper.py

# Expected output:
# 2026-01-31 14:23:45 - INFO - Fetching seasons from https://api.jugend-musiziert.org/api/seasons
# 2026-01-31 14:23:46 - INFO - Successfully scraped 28 seasons
# 2026-01-31 14:25:02 - INFO - Version 1706775000 created and saved

# Check results
ls -lh data/jugend_musiziert_data.json
cat data/versions.json
```

## Second Run: Incremental Scrape

```bash
# Run again (only scrapes new seasons by default - smart mode)
uv run scraper/scraper.py

# Expected output:
# 2026-02-05 09:10:00 - INFO - Checking for new seasons...
# 2026-02-05 09:10:01 - INFO - Found 2 new seasons: [2026, 2027]
# 2026-02-05 09:10:05 - INFO - Scraping only new seasons
# 2026-02-05 09:11:02 - INFO - Version 1707183000 created
```

## Common Commands

```bash
# Preview without scraping
uv run scraper/scraper.py --dry-run

# Force full re-scrape
uv run scraper/scraper.py --force

# Specific seasons only
uv run scraper/scraper.py --season-filter=2024,2025

# Specific region only
uv run scraper/scraper.py --region-filter=Bayern

# Open analysis notebook
jupyter lab analysis/analysis.ipynb
```

## Next Steps

1. Read [INSTRUCTIONS.md](INSTRUCTIONS.md) for coding standards and guidelines
2. See [doc/](doc/) for architecture documentation (ARC42 format)
3. Review [README.md](README.md) for project overview
4. Explore [analysis/analysis.ipynb](analysis/analysis.ipynb) for data exploration

## Troubleshooting

### "Python version" error
```bash
uv python install 3.14
uv sync
```

### "Module not found"
```bash
uv sync
```

### "Connection timeout"
- Check internet connection
- Verify API is reachable: `curl https://api.jugend-musiziert.org/api/seasons`
- Retry the scraper

### "data/ directory missing"
Scraper creates it automatically. If needed manually:
```bash
mkdir -p data/versions
```

### "JSON parse error"
Restore from snapshot:
```bash
ls data/versions/         # List available versions
cp data/versions/v{timestamp}.json data/jugend_musiziert_data.json
```

---

For more information, see [INSTRUCTIONS.md](INSTRUCTIONS.md) and [doc/](doc/).

