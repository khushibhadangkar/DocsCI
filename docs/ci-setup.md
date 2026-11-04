---
title: Continuous integration setup
description: Integrating DocsCI into GitHub Actions pull request checks and release tagging
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Continuous integration setup

Integrate DocsCI into automated workflows to prevent documentation regressions.

## Pull request workflow

DocsCI outputs native GitHub Actions workflow annotations using `--format github`. When rule violations occur, GitHub displays annotations directly on the pull request diff.

Create `.github/workflows/ci.yml` in your repository:

```yaml
name: Documentation CI

on:
  pull_request:
    paths:
      - 'docs/**'
      - 'sample_docs/**'
      - 'docsci/**'
      - 'tests/**'

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run code linter
        run: ruff check .

      - name: Run test suite
        run: pytest --cov=docsci --cov-report=term-missing

      - name: Lint documentation
        run: docsci lint docs/ --format github --strict

      - name: Validate links
        run: docsci links docs/ --format github --strict
```

## Release drafting workflow

When tagging a new software version, generate release notes and upload them as an artifact for human editorial review:

```yaml
name: Draft Release Notes

on:
  push:
    tags:
      - 'v*'

jobs:
  draft:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install DocsCI
        run: pip install -e .

      - name: Generate release notes draft
        run: docsci release-notes --to ${{ github.ref_name }} --ai-summary --output RELEASE_NOTES_DRAFT.md
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

      - name: Upload draft artifact
        uses: actions/upload-artifact@v4
        with:
          name: release-notes-draft
          path: RELEASE_NOTES_DRAFT.md
```
