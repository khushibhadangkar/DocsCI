# Changelog

All notable changes to DocsCI are documented in this file using Conventional Commits.

## [0.1.0] - 2026-11-04

### Added
- **core:** Initialize project scaffolding, data models, and pluggable rule registry.
- **lint:** Pluggable style rules (heading hierarchy, single H1, sentence-case, max sentence length, passive voice, banned phrases, imperative steps).
- **lint:** Terminology enforcement using `terminology.yml` dictionary.
- **lint:** Front matter metadata rules (required fields, YYYY-MM-DD date format, stale content warning threshold).
- **lint:** Multi-format reporters: ANSI table, structured JSON, and GitHub Actions annotations.
- **links:** Internal file and heading anchor resolution.
- **links:** External HTTP link validation with polite rate limiting, in-memory caching, timeouts, retries, and allowlist.
- **release-notes:** Conventional Commits parser and changelog generator producing lint-clean Markdown.
- **ai:** Gemini API client with offline mock fallback and versioned prompt management in `prompts/`.
- **ai:** Two-way claim verification engine and human accuracy gate generating `RELEASE_NOTES_DRAFT.md`.
- **report:** Documentation health summary reports and before/after comparison diff engine.
- **sample_docs:** 14 realistic backup-and-recovery product documentation topics.
- **docs:** Complete topic-based documentation suite and failure modes reference.
- **ci:** GitHub Actions pull request CI and tag-triggered release notes draft workflow.
