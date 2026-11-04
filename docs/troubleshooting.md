---
title: Troubleshooting guide
description: Solutions for common DocsCI linting, link checking, and API issues
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Troubleshooting guide

Diagnose and resolve common DocsCI configuration and execution problems.

## Linter issues

### Malformed YAML front matter

- **Symptom**: `front-matter-required` flags a malformed block on line 1.
- **Cause**: Syntax error between opening and closing `---` delimiters.
- **Solution**: Verify YAML indentation and ensure colon separators follow key names.

### False positive in code block

- **Symptom**: Rules trigger on banned words or passive voice inside code snippets.
- **Cause**: Unclosed code fences allow markdown parsers to treat code as prose.
- **Solution**: Ensure every opening code fence (` ``` `) has a matching closing fence.

## Link checker issues

### False broken report on valid external URL

- **Symptom**: External link reports HTTP 403 or 405 error.
- **Cause**: Some servers reject `HEAD` requests.
- **Solution**: Add the URL pattern to the `allowlist` in `docsci.yml` if the site blocks automated requests.

### Local anchor not recognized

- **Symptom**: Local anchor reports `#heading-anchor` not found.
- **Cause**: Heading anchor slug differs from manual link.
- **Solution**: Check that slugification matches GitHub standard lowercase hyphenated conventions.

## AI release summarizer issues

### Missing GEMINI_API_KEY environment variable

- **Symptom**: CLI warns that API key is unset.
- **Cause**: Environment variable `GEMINI_API_KEY` is not present in shell environment.
- **Solution**: Export your key (`export GEMINI_API_KEY="..."`) or omit the flag to use offline mock generation.
