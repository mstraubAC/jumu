# 2. Architecture Constraints

## 2.1 Technical Constraints

| Constraint | Rationale |
|-----------|-----------|
| Python 3.14+ required | Modern syntax, async improvements, type system stability |
| aiohttp for HTTP | Efficient async parallelization for API requests |
| Polars for data analysis | Superior performance and API clarity vs pandas |
| JSON for data storage | No schema migration, human-readable, API-native format |
| Unix timestamps for versions | Precise, monotonic, no timezone ambiguity |
| No ORM (SQLite/PostgreSQL) | JSON provides sufficient structure; versioning tracks history |

## 2.2 Organizational Constraints

| Constraint | Rationale |
|-----------|-----------|
| uv only for dependency management | Single tool, reproducible environments, faster than pip |
| Code documentation in INSTRUCTIONS.md | Single source of truth for developer guidance |
| ARC42 documentation in doc/ | Industry-standard structure; easy to maintain and extend |
| No markdown inflation | Readers prefer facts; document only what's necessary |

## 2.3 Deployment Constraints

| Constraint | Impact |
|-----------|--------|
| No external database required | Self-contained; runs anywhere with Python 3.14 |
| Data directory must exist | `uv run` creates if missing |
| API endpoint stability | If Jugend musiziert API changes, manual URL updates needed |

## 2.4 Quality Constraints

- **Type hints**: Mandatory for all public functions/classes
- **Docstrings**: Required for public APIs (one-line + detailed explanation)
- **Async-first**: Use async/await for I/O; sync only for CPU-bound ops
- **Error handling**: Log failures; don't silently fail
- **Test coverage**: Manual validation via examples; automated tests for critical paths

