# Helios CLI — Development Tasks
# Requires: uv (https://docs.astral.sh/uv/)

set dotenv-load := false

# Default: list available recipes
default:
    @just --list

# ── Setup ────────────────────────────────────────────────────────────

# Install all dependencies
sync:
    uv sync

# ── Testing ──────────────────────────────────────────────────────────

# Run all tests
test *args:
    uv run pytest {{ args }}

# Run tests for the library only
test-lib *args:
    uv run pytest tests/lib {{ args }}

# Run Home Assistant integration tests only
test-ha *args:
    uv run pytest tests/ha {{ args }}

# Run tests with coverage report
test-cov:
    uv run pytest --cov=custom_components.helios_kwl_ec300._core --cov=helios_cli --cov-report=term-missing

# ── Code Quality ─────────────────────────────────────────────────────

# Lint with ruff
lint:
    uv run ruff check custom_components/ helios_cli/ tests/

# Format with ruff
fmt:
    uv run ruff format custom_components/ helios_cli/ tests/

# Check formatting without modifying files
fmt-check:
    uv run ruff format --check custom_components/ helios_cli/ tests/

# Type-check with mypy
typecheck:
    uv run mypy custom_components/helios_kwl_ec300/_core helios_cli

# Run all checks (lint + format check + typecheck + tests)
check: lint fmt-check typecheck test

# Fix auto-fixable lint issues and format
fix:
    uv run ruff check --fix custom_components/ helios_cli/ tests/
    uv run ruff format custom_components/ helios_cli/ tests/

# ── Run ──────────────────────────────────────────────────────────────

# Run the helios CLI
run *args:
    uv run helios {{ args }}

# ── Cleanup ──────────────────────────────────────────────────────────

# Remove build artifacts and caches
clean:
    find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
    rm -rf dist/ build/ htmlcov/ .coverage
