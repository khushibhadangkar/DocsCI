---
title: Terminology list
description: Managing approved vocabulary and forbidden variants in terminology.yml
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Terminology list

Manage your organizational vocabulary in a centralized YAML dictionary.

## Dictionary structure

The `terminology.yml` file defines preferred terms alongside forbidden variants and explanations:

```yaml
terms:
  - preferred: "backup job"
    forbidden:
      - "backup task"
      - "backup routine"
      - "backup script"
    explanation: "Use 'backup job' to describe a configured backup operation or scheduled run."

  - preferred: "immutable storage"
    forbidden:
      - "write-once disk"
      - "worm storage"
    explanation: "Use 'immutable storage' when describing tamper-proof retention targets."
```

## Adding new terms

Follow this procedure to introduce a new term to the dictionary:

1. Open `terminology.yml` in your editor.
2. Add a new item under the `terms` list with preferred text, forbidden variants, and an explanation.
3. Run the linter to verify terminology across all documents:
   ```bash
   docsci lint docs/
   ```

The rule reports the exact line number, column, and suggested replacement for every flagged variant.
