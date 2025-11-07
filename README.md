# Compose

Minimal, dependency-free Markdown typesetting system.

## Installation

```bash
poetry install
```

## Usage

Using the `compose` executable:
```bash
poetry run compose build notes.md --config compose.toml
```

Or as a Python module:
```bash
poetry run python -m compose.cli build notes.md --config compose.toml
```

## Configuration

Example `compose.toml`:
```toml
mode = "document"
output = "pdf"
```
