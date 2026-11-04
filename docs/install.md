---
title: Installing DocsCI
description: System requirements and installation instructions for DocsCI
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Install DocsCI

Install DocsCI locally to check documentation before committing changes.

## System requirements

Before installing DocsCI, ensure your environment meets these criteria:

- Python 3.11 or higher
- Git version 2.30 or higher
- A standard virtual environment manager

## Installation procedure

Follow these steps to set up DocsCI in an editable virtual environment:

1. Clone the repository to your workstation.
2. Create an isolated virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install DocsCI in editable mode:
   ```bash
   pip install -e .
   ```
4. Verify the CLI installation:
   ```bash
   docsci --version
   ```

## Development tools

Install optional testing and code quality tools for local contribution:

```bash
pip install -e ".[dev]"
```
