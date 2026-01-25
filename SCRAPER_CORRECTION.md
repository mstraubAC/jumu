# Scraper Correction Summary

## ✅ Problem Fixed

The scraper was initially trying to extract data from the page structure instead of calling the actual tournament API endpoints.

## ✅ Solution Implemented

Updated `scraper.py` to directly call three main API endpoints:

### 1. **Seasons Endpoint**
- **URL**: `https://api.jugend-musiziert.org/api/seasons`
- **Method**: `fetch_seasons()`
- **Data Captured**: Tournament seasons (years, age groups, registration deadlines)

### 2. **Timetable Endpoint**
- **URL**: `https://api.jugend-musiziert.org/api/timetable`
- **Method**: `fetch_timetable()`
- **Data Captured**: Tournament timetable with:
  - Performance dates and times
  - Venues and rooms
  - Age groups and categories
  - Detailed program information (compositions, composers, durations)
  - Performer information (names, instruments, roles)

### 3. **Results Endpoint** (Next.js)
- **URL Pattern**: `https://www.jugend-musiziert.org/_next/data/{buildId}/de/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/{region_slug}/ergebnisse.json`
- **Method**: `fetch_results_for_region(region_slug)`
- **Feature**: Automatically extracts build ID from main page

## ✅ Code Changes

### Removed Outdated Methods:
- `_extract_api_base()` - Not needed, API endpoints are hardcoded
- `_find_api_endpoints()` - Not needed, endpoints are known
- `scrape_schedule()` - Replaced by `fetch_timetable()`

### Updated Classes/Methods:
- **fetch_seasons()** - Fetches actual season data
- **fetch_timetable()** - Fetches actual schedule/timetable data
- **fetch_results_for_region()** - Fetches region-specific results
- **scrape_tournament_data()** - Orchestrates all API calls
- **save_data()** - Updated to handle `Dict` instead of `List`

## ✅ Verification

The scraper now successfully captures real tournament data:

```json
{
  "metadata": {
    "timestamp": "2026-01-25 17:55:46.657822",
    "url": "https://www.jugend-musiziert.org/...",
    "region": "esslingen-goeppingen-und-rems-murr"
  },
  "seasons": {
    "@type": "hydra:Collection",
    "hydra:member": [
      {
        "id": 1,
        "year": 2024,
        "number": 61,
        "ageGroups": [...]
      },
      ...
    ]
  },
  "timetable": {
    "@type": "hydra:Collection",
    "hydra:member": [
      {
        "date": "2024-01-09",
        "room": {...},
        "category": "Duo: Klavier und ein Streichinstrument",
        "appointments": [
          {
            "startTime": "2024-01-09T09:40:00+00:00",
            "entry": {
              "programTitle": null,
              "programItems": [
                {
                  "title": "Sonata",
                  "opus": "op. 38/1",
                  "contributors": [...]
                },
                ...
              ],
              "appearances": [
                {
                  "person": {"firstName": "...", "lastName": "..."},
                  "instruments": [...]
                }
              ]
            }
          }
        ]
      },
      ...
    ]
  }
}
```

## 🎯 Result

The scraper now correctly collects:
- ✅ Tournament seasons and age groups
- ✅ Detailed timetable with performance schedules
- ✅ Participant information and performance details
- ✅ Venue and room information
- ✅ Composition and program details

All data is saved to `jugend_musiziert_data.json` in a well-structured Hydra API format.

## 📝 Running the Scraper

```bash
# Using uv:
uv run python scraper.py

# Using Python directly:
python3 scraper.py
```

The scraper will:
1. Fetch seasons data from the API
2. Fetch timetable/schedule data
3. Fetch results for the Esslingen region
4. Save all data to `jugend_musiziert_data.json`
