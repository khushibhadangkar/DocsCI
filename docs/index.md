---
title: DocsCI documentation
description: Architecture and workflows for DocsCI quality automation
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# DocsCI documentation

DocsCI provides docs-as-code quality and release automation for technical documentation.

## Overview

DocsCI combines deterministic static analysis with an AI-assisted release summarizer. The tool executes locally during authoring and runs inside continuous integration pipelines to safeguard documentation quality.

## Core capabilities

DocsCI provides four core documentation workflows:

- **Style and metadata linting**: Enforce style rules, metadata requirements, and terminology standards.
- **Link integrity verification**: Check internal anchor targets and validate external hyperlinks with retries.
- **Release notes generation**: Assemble changelogs from Git Conventional Commits into clean Markdown.
- **Verified release summaries**: Generate customer summaries using Gemini and audit claims against commit evidence.

## Next steps

Explore the documentation guides below:

- [Installation](install.md): Install the CLI and dependencies.
- [Quickstart](quickstart.md): Run your first lint and link checks in 60 seconds.
- [Configure rules](configure-rules.md): Customize rule severities and options.
- [CLI reference](cli-reference.md): Review flags and arguments for every command.
