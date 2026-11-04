---
title: Release notes workflow
description: Conventional commits aggregation and changelog generation workflow
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Release notes workflow

Automate changelog assembly from structured Git history.

## Conventional commits format

DocsCI parses commit messages structured according to the Conventional Commits specification:

- `feat(scope): Description (#123)` maps to **Added**
- `fix(scope): Description (#124)` maps to **Fixed**
- `perf(scope): Description` maps to **Performance Improvements**
- `docs(scope): Description` maps to **Documentation**
- `feat(api)!: Description` maps to **Breaking Changes**

## Generating release notes

Generate release notes between two Git revisions:

```bash
docsci release-notes --from v1.0.0 --to v1.1.0 --output docs/release-notes-v1.1.0.md
```

## Lint clean guarantee

The generated Markdown file includes valid YAML front matter and sentence-case headings. The output passes the DocsCI style and metadata linter without requiring manual reformatting.
