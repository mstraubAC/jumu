# 11. Technical Risks

## 11.1 API Stability Risk

**Risk**: Jugend musiziert API changes structure, endpoints, or authentication.

**Impact**: High. Scraper becomes non-functional.

**Probability**: Medium (APIs evolve every 1-2 years).

**Mitigation**:
- Maintain fallback scraper (scraper_selenium.py) for HTML parsing
- Log all API responses; easy to spot schema changes
- Version snapshots preserve historical structure
- Alert when API response diverges from expected schema

**Detection**:
- JSON parsing errors in logs
- Unexpected keys/missing fields
- API rate-limit changes (429 responses)

**Recovery**:
1. Inspect latest raw API response
2. Update parser if schema changed
3. Re-run with --force to re-scrape with new parser

---

## 11.2 Data Loss Risk

**Risk**: Accidental overwrite of current data during scrape.

**Impact**: High. Lost all versions.

**Probability**: Low (snapshots protect; --force requires explicit action).

**Mitigation**:
- Automatic versioning creates snapshot before overwrite
- data/versions/ immutable (never deleted)
- data/jugend_musiziert_data.json always has backup via latest snapshot
- Require --force flag for full re-scrape

**Detection**:
- File modification timestamps
- Version index shows gap in timestamps
- Snapshot count changes unexpectedly

**Recovery**:
```bash
# Restore from snapshot if main file corrupted
cp data/versions/v{timestamp}.json data/jugend_musiziert_data.json
```

---

## 11.3 Concurrency Issues Risk

**Risk**: Async operations race condition or deadlock.

**Impact**: Medium. Scrape hangs or returns incomplete data.

**Probability**: Low (asyncio well-tested, simple gather pattern).

**Mitigation**:
- Use asyncio.gather() with explicit exception handling
- Timeout on all aiohttp requests (10s)
- Log all concurrent operations start/end
- Test with --dry-run before full scrape

**Detection**:
- Timeout logs with "Timeout" error
- Missing expected data (e.g., season not in result)
- Scraper process hangs >60s

**Recovery**:
1. Kill scraper (Ctrl+C)
2. Check logs for timeout or exception
3. Retry with --force to reset state

---

## 11.4 Version History Corruption Risk

**Risk**: versions.json or version snapshots become corrupted (disk failure, crash mid-write).

**Impact**: Medium. Can't replay or recover versions.

**Probability**: Low (atomic writes, modern filesystems).

**Mitigation**:
- Write to temporary file, then atomic rename
- Verify JSON syntax after write
- Keep multiple snapshots (monthly backups)
- Git-commit versions.json regularly

**Detection**:
- JSON parse error when loading versions.json
- Missing version snapshot files
- Timestamp gaps in version history

**Recovery**:
```bash
# Restore versions.json from git
git checkout data/versions.json

# Restore missing snapshot from git
git checkout data/versions/v{timestamp}.json
```

---

## 11.5 Memory/Performance Degradation Risk

**Risk**: Large dataset accumulation causes scraper memory/time to grow unbounded.

**Impact**: Low-Medium. Scraper becomes slow (not broken).

**Probability**: Low (datasets grow slowly, analyzed incrementally).

**Mitigation**:
- Monitor data/jugend_musiziert_data.json size (warn if >1GB)
- Profile async operations (log request durations)
- Lazy normalization in analysis (don't load all seasons at once)
- Archive old snapshots monthly if >100 versions

**Detection**:
- File size check: `ls -lh data/jugend_musiziert_data.json`
- Scrape duration increases >20s
- Memory usage >500MB

**Recovery**:
```bash
# Archive old versions (keep last 12)
rm data/versions/v{old_timestamps}.json
```

---

## 11.6 External Dependency Risk

**Risk**: Critical dependency (aiohttp, Polars) becomes unmaintained or introduces breaking changes.

**Probability**: Low (both are widely-used, active).

**Mitigation**:
- Pin versions in pyproject.toml
- Test against new versions before upgrading
- Have fallback implementations (httpx for aiohttp, pandas for Polars)
- Keep 2-3 major versions support in pyproject.toml

**Detection**:
- Dependency security advisory (GitHub, PyPI)
- Build failure on new major version
- Unexpected behavior in analysis

**Recovery**:
```bash
# Rollback to working version
uv pip install aiohttp==3.9.1  # Specific version
```

---

## 11.7 Deployment Complexity Risk

**Risk**: uv or Python environment issues prevent scraper execution on CI/CD or new machines.

**Probability**: Low (uv handles environments well).

**Mitigation**:
- GETTING_STARTED.md documents setup clearly
- uv.lock pins all transitive dependencies
- Docker image option for CI/CD
- Regular testing on clean environments

**Detection**:
- `uv sync` fails
- Python 3.14 not found
- Module import errors

**Recovery**:
```bash
# Force environment refresh
rm -rf .venv uv.lock
uv sync --python 3.14
```

---

## 11.8 Risk Matrix

| Risk | Impact | Probability | Priority | Mitigation Effort |
|------|--------|-------------|----------|-------------------|
| API changes | High | Medium | **CRITICAL** | Medium |
| Data loss | High | Low | **HIGH** | Low |
| Concurrency bugs | Medium | Low | MEDIUM | Low |
| Version corruption | Medium | Low | MEDIUM | Low |
| Memory degradation | Low | Low | LOW | Low |
| Dependency issues | Medium | Low | MEDIUM | Low |
| Deployment issues | Medium | Low | MEDIUM | Low |

**Priority Actions**:
1. **CRITICAL**: Document API endpoint changes; test fallback scraper weekly
2. **HIGH**: Automate version snapshots; test recovery monthly
3. **MEDIUM**: Add memory profiling; monitor with alerts

