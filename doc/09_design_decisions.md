# 9. Design Decisions

## 9.1 Why aiohttp Instead of requests?

**Decision**: Use aiohttp for HTTP client in scraper.

**Context**: Scraper needs to fetch multiple API endpoints (seasons, timetable, participants) for multiple seasons/regions.

**Options**:
1. **requests** (synchronous) — Easy to use, mature, simple logic
2. **httpx** (async or sync) — Modern, similar to requests, async support
3. **aiohttp** (async only) — Lightweight, battle-tested, connection pooling

**Decision**: aiohttp

**Rationale**:
- Fetching 3 seasons × 5 endpoints = 15 API calls in parallel → ~50% time savings
- aiohttp's connection pool reuses TCP connections → network efficiency
- Maturity and stability well-proven in production systems
- Minimal overhead vs httpx for our simple use case

**Trade-off**: Requires async/await throughout scraper code (accepted complexity).

## 9.2 Why Polars for Analysis?

**Decision**: Use Polars instead of pandas for data analysis.

**Context**: analysis.ipynb needs to load JSON, normalize to tables, query interactively.

**Options**:
1. **pandas** — Ubiquitous, huge community, familiar to many
2. **Polars** — 10x faster, better API, lazy evaluation, better null handling
3. **SQL** (DuckDB/SQLite) — Powerful queries, but requires schema definition

**Decision**: Polars

**Rationale**:
- Performance: Polars lazy evaluation means filtering happens before load
- API: `.select()`, `.filter()` more intuitive than pandas `.loc[]`/`.iloc[]`
- Null handling: Polars treats null as distinct from 0/empty string (correct)
- Memory: Arrow format more efficient than numpy arrays
- No additional infrastructure (DuckDB requires system setup)

**Trade-off**: Smaller ecosystem than pandas; fewer pre-built libraries.

## 9.3 Why JSON Storage (Not Relational DB)?

**Decision**: Store data as JSON files, normalize at analysis time (no PostgreSQL).

**Context**: Need to persist scraped data persistently and support version tracking.

**Options**:
1. **JSON files** — API native, version-control friendly, simple
2. **SQLite** — Structured, queryable, local file
3. **PostgreSQL** — Powerful, multi-user, overkill for single user
4. **Parquet files** — Efficient columnar storage, schema-enforced

**Decision**: JSON files + Polars normalization

**Rationale**:
- API returns JSON natively; no serialization overhead
- JSON is git-friendly (easy diffs, version control)
- No schema migration when API structure evolves
- Polars reads JSON efficiently → no performance penalty
- Snapshot-based versioning is simpler with files than DB
- Lower operational complexity (no DB server needed)

**Trade-off**: Raw JSON is schema-less; analysis code must validate structure.

## 9.4 Why Unix Timestamps for Versions?

**Decision**: Use Unix timestamp (seconds since epoch) as version ID.

**Context**: Need to track when data was scraped, enable historical queries.

**Options**:
1. **UUID** (v4 random) — Unique, distributed-friendly
2. **Sequential integer** — Simple, but requires centralized counter
3. **Unix timestamp** — Temporal ordering, human-readable, timezone-free
4. **Semantic version** (1.2.3) — Marketing-friendly, but subjective

**Decision**: Unix timestamp

**Rationale**:
- Automatically ordered by scrape time (no need for separate sort field)
- Human-readable: `1706775000` → 2026-01-31 14:23:00 UTC
- Precise to second (sufficient granularity)
- No timezone confusion (always UTC)
- Queryable: "all versions after date X" is simple comparison

**Trade-off**: Requires conversion for human display (minor).

## 9.5 Why Lazy Normalization (Not Pre-Normalized DB)?

**Decision**: Store raw JSON, normalize at analysis time (not in scraper).

**Context**: Data is multi-structured (seasons, timetables, participants) with many possible queries.

**Options**:
1. **Pre-normalized in scraper** — Create SQL tables before storage
2. **Lazy normalization** — Store raw JSON, normalize on-demand in analysis
3. **Hybrid** — Pre-normalize common tables, raw JSON for rest

**Decision**: Lazy normalization

**Rationale**:
- Different analyses may need different normalizations
- Preserves original API structure for debugging
- Easier to add new analyses without restructuring data
- Polars is fast enough for real-time normalization
- No risk of data loss during normalization

**Trade-off**: Analysis code must handle raw JSON validation; slightly slower first-run.

## 9.6 Why Python 3.14+ (Not 3.8)?

**Decision**: Target Python 3.14+ for new code (support 3.8+ for backward compatibility).

**Context**: Need modern language features, type safety, performance.

**Options**:
1. **Python 3.8** — Wide availability, backward compatible
2. **Python 3.11** — Type system improvements, performance gains
3. **Python 3.14+** — Latest features, best performance

**Decision**: Target 3.14+, allow fallback to 3.8

**Rationale**:
- Type system stable and feature-complete (PEP 675, 696)
- Async performance improvements matter for scraper
- Match current best-practice Python development
- uv makes older versions installable on any system

**Trade-off**: May require minor adjustments on legacy systems; acceptable.

