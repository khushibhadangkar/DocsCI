---
title: Configuring rules
description: Customize linting rules, severities, and link options in docsci.yml
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Configuring rules

Configure DocsCI behavior through the `docsci.yml` file in your repository root.

## Configuration structure

The configuration file contains sections for rules, link checking, and release note settings.

```yaml
version: 1

rules:
  heading-hierarchy:
    enabled: true
    severity: error

  max-sentence-length:
    enabled: true
    severity: warning
    max_words: 30

  banned-phrases:
    enabled: true
    severity: warning
    phrases:
      - simply
      - just
      - easy
      - obviously

links:
  timeout_seconds: 5
  retries: 2
  slow_threshold_seconds: 2.0
  allowlist:
    - "https://example.com"
```

## Rule severities

DocsCI supports three distinct severity tiers:

- **error**: Violations exit with code 1 and block continuous integration builds.
- **warning**: Violations report as warnings. Strict mode elevates warnings to failures.
- **info**: Informational notices that do not cause build failures.

## Disabling a rule

To disable a rule, set its enabled property to false in `docsci.yml`:

```yaml
rules:
  passive-voice:
    enabled: false
```
