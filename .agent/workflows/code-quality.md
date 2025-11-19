---
description: Run code quality checks with ruff and mypy
---

# Code Quality Checks Workflow

This workflow runs periodic code quality checks using ruff and mypy to maintain a clean codebase.

## Quick Check (Recommended)

Run both tools to get a quick overview:

```bash
# Run ruff check
poetry run ruff check src/ tests/

# Run mypy on source code only
poetry run mypy src/
```

## Detailed Analysis

### Ruff - Linting and Style

Check with statistics to see error distribution:

```bash
poetry run ruff check src/ tests/ --statistics
```

Auto-fix safe issues:

```bash
poetry run ruff check --fix src/ tests/
```

Auto-fix including unsafe fixes (review changes carefully):

```bash
poetry run ruff check --fix --unsafe-fixes src/ tests/
```

### Mypy - Type Checking

Run mypy on source code:

```bash
poetry run mypy src/
```

For more verbose output:

```bash
poetry run mypy src/ --show-error-codes --pretty
```

## Current Status

**Baseline (as of 2025-11-19):**
- Ruff: 634 errors remaining (down from 2474 after auto-fix)
  - Most common: N806 (naming), UP031 (printf formatting), N802 (function names)
  - 220 additional fixes available with `--unsafe-fixes`
- Mypy: Running successfully, type errors present but non-blocking
  - Tests excluded from checking to avoid module conflicts
  - Permissive configuration to allow gradual typing

## Configuration

Both tools are configured in `pyproject.toml`:

- **Ruff**: Line length 100, Python 3.12, multiple rule sets enabled
- **Mypy**: Python 3.12, permissive mode, tests excluded

## Periodic Maintenance

Run these checks:
1. **Before commits**: Quick check with `poetry run ruff check src/`
2. **Weekly**: Full check with statistics to track progress
3. **Before releases**: Full check + mypy + test suite

## Ignoring Specific Issues

If you need to ignore specific issues:

**Ruff** - Add inline comment:
```python
# ruff: noqa: E501
long_line_that_should_not_be_checked()
```

**Mypy** - Add inline comment:
```python
result = some_untyped_function()  # type: ignore[attr-defined]
```

## Goals

- Gradually reduce ruff errors by fixing issues during regular development
- Add type hints progressively to improve mypy coverage
- Keep test suite passing after any refactoring
