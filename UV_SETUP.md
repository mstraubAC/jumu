# uv Setup Guide

## What is uv?

[uv](https://docs.astral.sh/uv/) is an extremely fast Python package installer and resolver, written in Rust. It's a modern replacement for pip with better performance and dependency management.

**Benefits of uv**:
- ⚡ 10-100x faster than pip
- 🔒 Better dependency resolution
- 📦 Lock file support (uv.lock)
- 🎯 Built-in project management
- 🐍 Python version management

---

## Installation

### Install uv

```bash
# Using pip (fastest)
pip install uv

# Or using homebrew (macOS)
brew install uv

# Or using curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or from source
https://docs.astral.sh/uv/getting-started/
```

### Verify Installation

```bash
uv --version
```

---

## Quick Start with This Project

### Step 1: Navigate to Project
```bash
cd /Users/marcel/projects/jumu
```

### Step 2: Install Dependencies
```bash
uv sync
```

This will:
- Read `pyproject.toml` for dependencies
- Install all required packages
- Create a virtual environment (if needed)
- Generate `uv.lock` for reproducible installs

### Step 3: Run the Scraper
```bash
uv run python scraper.py
```

---

## Common uv Commands

### Project Management
```bash
# Install all dependencies
uv sync

# Install with optional dependencies
uv sync --extra selenium              # Install Selenium support
uv sync --all-extras                  # Install all optional deps
uv sync --extra selenium --extra data-science

# Update dependencies
uv sync --upgrade

# Add a new package
uv add requests
uv add -d pytest                     # Add as dev dependency

# Remove a package
uv remove requests

# Show installed packages
uv pip list
```

### Running Scripts
```bash
# Run a script in the project environment
uv run python scraper.py
uv run python data_processor.py jugend_musiziert_data.json

# Run with arguments
uv run python examples.py 1
```

### Virtual Environment
```bash
# Activate the project virtual environment
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Deactivate
deactivate

# View environment info
uv venv
```

### Python Version Management
```bash
# Specify Python version
uv python install 3.11
uv run --python 3.11 python scraper.py

# List available versions
uv python list
```

---

## Project Configuration (pyproject.toml)

Your project includes a modern `pyproject.toml` with:

### Core Dependencies
```toml
dependencies = [
    "requests>=2.28.0",
    "beautifulsoup4>=4.11.0",
]
```

### Optional Dependencies
```toml
[project.optional-dependencies]
selenium = ["selenium>=4.0.0"]
scheduler = ["APScheduler>=3.10.0"]
data-science = ["pandas>=1.3.0", "openpyxl>=3.7.0"]
dev = ["pytest>=7.0.0", "black>=22.0.0", "mypy>=0.950"]
```

### Tool Configurations
- **black**: Code formatter settings
- **isort**: Import sorting settings  
- **mypy**: Type checking settings

---

## Typical Workflow

### First Time Setup
```bash
# Clone/navigate to project
cd /Users/marcel/projects/jumu

# Install uv
pip install uv

# Install project dependencies
uv sync
```

### Daily Usage
```bash
# Run the scraper
uv run python scraper.py

# Process data
uv run python data_processor.py jugend_musiziert_data.json --csv output.csv

# Run examples
uv run python examples.py
```

### Adding Dependencies
```bash
# Add a new package
uv add package-name

# Add a dev tool
uv add -d black

# The files are automatically updated:
# - pyproject.toml (new dependency added)
# - uv.lock (updated with exact versions)
```

### Team Collaboration
```bash
# Share your environment
# Everyone uses: uv sync (installs exact versions from uv.lock)

# Update shared dependencies
uv sync --upgrade
```

---

## uv.lock File

The `uv.lock` file (if generated) contains exact versions of all dependencies and their dependencies. This ensures reproducible installs across machines.

**Benefits**:
- ✅ Everyone installs the exact same versions
- ✅ More secure (all hashes verified)
- ✅ Faster subsequent installs
- ✅ Better for CI/CD pipelines

**Usage**:
```bash
# Commit to git for reproducibility
git add uv.lock
git commit -m "Lock dependencies"

# Others use:
uv sync  # Installs exact versions from uv.lock
```

---

## Installation Methods Comparison

| Method | Speed | Easy | Modern | Recommended |
|--------|-------|------|--------|-------------|
| **uv** | ⚡⚡⚡ | ✅ | ✅ | **✅ YES** |
| pip | ⚡ | ✅ | ⚠️ | OK |
| Conda | ⚡ | ✅ | ⚠️ | OK |
| Poetry | ⚡⚡ | ⚠️ | ✅ | OK |

---

## Troubleshooting

### uv Not Found
```bash
# Ensure uv is in PATH
which uv

# If not found, reinstall
pip install --upgrade uv
```

### Virtual Environment Issues
```bash
# Reset virtual environment
rm -rf .venv
uv sync

# Or use system Python
uv run --python system python scraper.py
```

### Dependency Conflicts
```bash
# Update all dependencies
uv sync --upgrade

# Clean and reinstall
rm uv.lock
uv sync
```

### Permission Errors
```bash
# Run with appropriate permissions
sudo uv sync

# Or install to user site-packages
uv pip install --user package-name
```

---

## Advanced Usage

### Using with Docker
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Copy project files
COPY . /app
WORKDIR /app

# Install dependencies
RUN uv sync --no-dev

# Run scraper
CMD ["uv", "run", "python", "scraper.py"]
```

### Using with CI/CD
```yaml
# GitHub Actions example
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync
      
      - name: Run scraper
        run: uv run python scraper.py
```

### Virtual Environment in Project
```bash
# Create venv in project directory
uv venv

# Activate
source .venv/bin/activate

# Or run commands directly
uv run python script.py
```

---

## Learning More

- **Official Docs**: https://docs.astral.sh/uv/
- **GitHub**: https://github.com/astral-sh/uv
- **Comparison with pip**: https://docs.astral.sh/uv/pip/
- **Project Configuration**: https://docs.astral.sh/uv/concepts/projects/

---

## Migration from pip

### From requirements.txt to uv

If you have a `requirements.txt`:

```bash
# uv can read it and update pyproject.toml
uv pip compile requirements.txt

# Or manually create pyproject.toml (already done for this project)
```

### Keeping Both

This project keeps both:
- **pyproject.toml**: For uv (modern, recommended)
- **requirements.txt**: For pip (traditional, compatibility)

You can use either method:
```bash
# Modern approach with uv
uv sync

# Traditional approach with pip
pip install -r requirements.txt
```

---

## FAQ

**Q: Is uv production-ready?**
A: Yes! It's stable and used in many production projects.

**Q: Can I use uv with existing pip projects?**
A: Yes! uv is compatible with pip and can install from PyPI.

**Q: What about virtual environments?**
A: uv creates and manages them automatically. You can also use venv manually.

**Q: Is it safe to use uv for my project?**
A: Yes! It verifies all package hashes and has excellent security practices.

**Q: Can I switch back to pip?**
A: Absolutely! Both pyproject.toml and requirements.txt are preserved.

---

## Next Steps

1. ✅ Install uv: `pip install uv`
2. ✅ Sync dependencies: `uv sync`
3. ✅ Run scraper: `uv run python scraper.py`
4. 📚 Read uv docs: https://docs.astral.sh/uv/
5. 🚀 Use for all your Python projects!

---

**Happy scraping with uv! 🎵⚡**
