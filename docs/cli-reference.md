---
title: CLI reference
description: Complete command-line interface reference for the docsci command
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# CLI reference

Reference guide for all DocsCI commands, options, and exit codes.

## Global options

- `--version`, `-v`: Display DocsCI version and exit.
- `--help`: Show available commands and options.

## docsci lint

Scan Markdown documentation files against style, terminology, and metadata rules.

```bash
docsci lint <path> [options]
```

### Options

- `<path>` (required): File path or directory containing `.md` files.
- `--config`, `-c`: Path to custom `docsci.yml`.
- `--terminology`, `-t`: Path to custom `terminology.yml`.
- `--format`, `-f`: Output format: `table` (default), `json`, or `github`.
- `--strict`: Exit with code 1 if DocsCI detects warnings in addition to errors.

## docsci links

Validate internal file targets, local anchors, and external HTTP hyperlinks.

```bash
docsci links <path> [options]
```

### Options

- `<path>` (required): File path or directory to scan.
- `--config`, `-c`: Path to `docsci.yml`.
- `--format`, `-f`: Output format: `table`, `json`, or `github`.
- `--strict`: Fail on redirected or slow links as well as broken ones.

## docsci release-notes

Generate Conventional Commits changelog from Git history.

```bash
docsci release-notes [options]
```

### Options

- `--from`: Starting Git tag or commit hash.
- `--to`: Target Git tag or commit hash (defaults to `HEAD`).
- `--repo`: Path to Git repository (defaults to `.`).
- `--output`, `-o`: File destination for generated release notes.
- `--ai-summary`: Trigger Gemini customer summary generation with claim verification.
- `--allow-unsupported`: Suppress failure exit code when DocsCI detects unsupported claims.
- `--config`, `-c`: Path to `docsci.yml`.

## docsci report

Produce a documentation health summary report with before and after comparison diffs.

```bash
docsci report [path] [options]
```

### Options

- `[path]`: Target documentation directory (defaults to `docs`).
- `--config`, `-c`: Path to `docsci.yml`.
- `--previous`, `-p`: Path to previous report JSON file for comparison.
- `--output`, `-o`: File path to write Markdown or JSON report to.

## Exit codes

- `0`: Success (all checks passed or clean run).
- `1`: Validation failure (lint errors, broken links, or unverified AI claims).
- `2`: Command invocation error (file or directory not found).
