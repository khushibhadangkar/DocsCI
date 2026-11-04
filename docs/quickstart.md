---
title: Quickstart guide
description: Get started with DocsCI quality checks in under sixty seconds
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Quickstart guide

Learn how to lint files, check links, and build release notes in under sixty seconds.

## Lint your documentation

Run the linter on your documentation directory:

```bash
docsci lint docs/
```

To fail on warnings as well as errors in automated builds, pass the strict flag:

```bash
docsci lint docs/ --strict
```

## Validate internal and external links

Check internal heading anchors and external URLs:

```bash
docsci links docs/
```

The checker validates that internal markdown links point to existing files and valid anchors.

## Generate release notes

Build release notes from your Git commit history:

```bash
docsci release-notes --from v1.0.0 --to HEAD
```

To produce an AI-assisted summary draft with claim verification, pass the summary flag:

```bash
docsci release-notes --ai-summary
```

Inspect the generated `RELEASE_NOTES_DRAFT.md` file before publication.
