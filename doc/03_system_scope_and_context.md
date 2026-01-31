# 3. System Scope and Context

## 3.1 Business Context

### External System Dependencies

| System | Interface | Purpose |
|--------|-----------|---------|
| Jugend musiziert API | REST/JSON | Fetch seasons, timetables, participants |
| Jugend musiziert Website | HTML/JavaScript | Fallback scraping if API changes |
| Local Filesystem | File I/O | Store versioned datasets |

### Users and Use Cases

1. **Data Analyst**: Runs `analysis.ipynb` to explore historical tournament data
2. **Scraper Operator**: Runs `uv run scraper/scraper.py` to capture new seasons
3. **Researcher**: Exports normalized tables via Polars for external analysis

## 3.2 Technical Context

### Input
- Jugend musiziert API endpoints (REST JSON)
- Website HTML (fallback)

### Output
- `data/jugend_musiziert_data.json` — Combined master dataset
- `data/versions/v{timestamp}.json` — Versioned snapshots
- `data/versions.json` — Version index with metadata

### Technical Environment
- Python 3.14+
- aiohttp for async HTTP parallelization
- Polars for data transformation
- Jupyter for interactive analysis
- uv for dependency management

## 3.3 Data Scope

The system manages the following data entities:

- **Seasons**: Competition years and age groups
- **Timetables**: Scheduled competition sessions (venue, date, time)
- **Appointments**: Individual competition appointments within timetables
- **Program Items**: Musical pieces (opus, composer, duration, style)
- **Persons**: Participants (name, city, country)
- **Instruments**: Musical instruments played
- **Appearances**: Links persons to instruments in specific performances
- **Contests**: Administrative competition identifiers

Data relationships are normalized to enable efficient querying and analysis.

