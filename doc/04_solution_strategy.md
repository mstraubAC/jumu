# 4. Solution Strategy

## 4.1 Architecture Pattern: Layered with Smart Data Pipeline

```
CLI / User Interface
        ↓
    Scraper Layer (async, parallel fetches)
        ↓
    Versioning Layer (smart detection, history tracking)
        ↓
    Storage Layer (JSON files, versioned snapshots)
        ↓
    Analysis Layer (Polars DataFrames, exploration)
```

## 4.2 Key Design Decisions

### 1. Async/Await Over Threading
**Decision**: Use aiohttp for all HTTP I/O (scraper).

**Rationale**: 
- Concurrent API requests without thread overhead
- Simpler error handling and cancellation
- Better CPU efficiency for network-bound operations

### 2. Versioning via Unix Timestamps
**Decision**: Track scraped data by Unix timestamp (seconds since epoch).

**Rationale**:
- Precise, monotonic, timezone-free
- Easy to query "all data after X"
- Human-readable (seconds → readable date)
- Database-independent

### 3. Smart Scraping (Default Incremental)
**Decision**: By default, scrape only new seasons/regions (no full re-scrape).

**Rationale**:
- Reduces API load
- Faster execution for operators
- Prevents accidental duplicate storage
- Manual `--force` flag allows full refresh when needed

### 4. JSON Storage (Not Relational DB)
**Decision**: Store raw data as JSON; normalize at analysis time.

**Rationale**:
- API returns JSON natively; no impedance mismatch
- Version control friendly (diff-able)
- No schema migration overhead
- Flexible for evolving API structure
- Polars easily reads JSON → DataFrames on demand

### 5. Lazy Normalization (Analysis Time)
**Decision**: Store raw JSON; normalize to DataFrames in analysis notebooks.

**Rationale**:
- Preserves original data structure
- Different analyses may need different normalizations
- Easier to debug and reconstruct data
- Polars is fast enough for real-time normalization

## 4.3 Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API endpoint changes | version history allows rollback; manual intervention documented |
| Data corruption | Versioned snapshots provide recovery points |
| Accidental full re-scrape | `--force` flag requires explicit action; smart mode default |
| Memory exhaustion | Async streams avoid loading all data at once |
| Missing seasons | detect_seasons_and_regions() logs all available options |

## 4.4 Technology Choices Rationale

| Component | Choice | Alternative | Reason |
|-----------|--------|-------------|--------|
| HTTP Client | aiohttp | httpx | aiohttp mature, widely trusted |
| Data Frame | Polars | pandas | 10x faster, better API, lazy evaluation |
| Dependency Mgr | uv | pip/poetry | Single tool, deterministic, fast |
| Storage Format | JSON | Parquet | API native, version control friendly |
| Version ID | Unix TS | UUID/Seq | Temporal ordering, human readable |

