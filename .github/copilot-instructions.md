# Project Instructions

## Project Overview

**jumu** is a data scraping and analysis platform for the Jugend musiziert (German youth music competition) dataset. It extracts structured tournament data from the official website and provides tools for comprehensive analysis of participation patterns, competition results, and musical repertoire across multiple seasons and age groups.

The project architecture separates concerns into three main domains: **scraping** (web data acquisition with smart versioning), **data organization** (structured storage and normalization), and **analysis** (exploratory data science using Polars). The system maintains a complete version history of scraped data, enabling incremental updates and safe re-scraping of specific seasons or regions without data loss.

Development prioritizes production-ready code with modern Python practices, efficient parallelization where beneficial, and documentation that precisely describes system architecture without inflation.

## Documentation Structure

**Root level** contains only:
- `README.md` — Project overview and quick start
- `GETTING_STARTED.md` — Setup and first-run instructions
- `INSTRUCTIONS.md` — This file (developer guidelines)

**All other documentation** lives in `doc/` directory following **ARC42 architecture documentation structure**:

### Core Architecture (ARC42 sections 1-11)
- `doc/01_introduction_and_goals.md` — Project purpose and success criteria
- `doc/02_architecture_constraints.md` — Technical and organizational constraints
- `doc/03_system_scope_and_context.md` — System boundaries and external interfaces
- `doc/04_solution_strategy.md` — Top-level solution approach
- `doc/05_building_block_view.md` — Component decomposition and interfaces
- `doc/06_runtime_view.md` — Dynamic behavior and component interactions
- `doc/07_deployment_view.md` — Infrastructure and deployment architecture
- `doc/08_crosscutting_concepts.md` — Patterns, standards, and conventions
- `doc/09_design_decisions.md` — Rationale for major technical choices
- `doc/10_quality_requirements.md` — Non-functional requirements
- `doc/11_technical_risks.md` — Known technical risks and mitigation

### Appendices (Reference material only)
- `doc/A1_versioning_system.md` — Technical guide to smart scraping and version management
- `doc/A2_api_reference.md` — Public API documentation and configuration reference

**Documentation principle**: Precise, fact-based content. No fluff. No duplication. Every file serves a unique purpose. Focus on **data structure architecture and relationships** — entity models, normalization strategy, and inter-module data contracts.

## The Scraper

The scraper is a **modern Python CLI application** with the following characteristics:

- **CLI-first design**: Command-line interface for all operations (run via `uv run scraper/scraper.py`)
- **Async parallelization**: Uses `aiohttp` for concurrent HTTP requests where feasible (e.g., fetching multiple seasons in parallel)
- **Smart versioning**: Tracks scraped data by Unix timestamp, automatically detects new seasons/regions, supports forced re-scraping
- **No external dependencies** for core scraping logic beyond aiohttp and standard library where possible
- **Structured output**: JSON format with normalized data ready for analysis

## Coding Guidelines

### Python Version & Syntax
- **Target**: Python 3.14 (modern syntax and features)
- Use type hints throughout (`from typing import ...` or native 3.10+ syntax)
- Use async/await patterns for I/O-bound operations

### Async & Concurrency
- Use `async`/`await` for HTTP requests, file I/O, and network operations
- Use `aiohttp` for HTTP parallelization in the scraper
- Prefer `asyncio` for concurrency orchestration
- Non-blocking operations only; avoid thread-based parallelization for I/O

### Data Analysis
- **Use Polars** for all data transformation, filtering, and analysis
- Polars is preferred over pandas for: performance, API clarity, null handling, and lazy evaluation
- Keep analysis notebooks (`analysis.ipynb`) as exploratory work; move production analysis to modules

### Repository Structure
- **Root level**: Only documentation and configuration files (no source code)
  - Documentation: `README.md`, `GETTING_STARTED.md`, `INSTRUCTIONS.md`
  - Configuration: `pyproject.toml`, `requirements.txt`, `config.json`
- **scraper/**: Web scraping logic, versioning, and CLI
- **analysis/**: Data transformation and analysis utilities
- **data/**: Data artifacts and version history (not in version control)
- **doc/**: Architecture and design documentation (ARC42 format)

### Quality Standards
- All public functions/classes require docstrings
- Type hints are mandatory for function signatures
- Use descriptive variable names; avoid single-letter variables except loop counters
- Prefer explicit over implicit; avoid excessive abstraction for one-time code
- Comment *why*, not *what* — code shows what it does

### Import Organization
```python
# Standard library
import json
import asyncio
from pathlib import Path
from typing import Optional

# Third-party
import aiohttp
import polars as pl

# Local
from scraper.version_manager import VersionManager
```

## Version Control

- `.gitignore` excludes: `data/`, `__pycache__/`, `*.pyc`, virtual environments
- Data files are artifacts, not source code; regenerate via scraper
- Documentation and code are the source of truth

## Testing & Validation

- Use `uv run` for consistent Python environment management
- Validate scraper output structure matches expected schema
- Test async operations in isolation before integration
- Profile scraper performance; target <30 second full-data acquisition

---

**Last updated**: 2026-01-31  
**Maintained by**: Project contributors
