"""Core documentation linting engine."""

from __future__ import annotations

import logging
from pathlib import Path

from docsci.models import DocsCIConfig, RuleContext, Violation
from docsci.rules import BaseRule, RuleRegistry
from docsci.utils.markdown_parser import parse_front_matter

logger = logging.getLogger(__name__)

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
    "build",
    "dist",
    "__pycache__",
}


def collect_markdown_files(target: Path) -> list[Path]:
    """Discover all .md markdown files within target path, excluding common directories."""
    if target.is_file():
        return [target] if target.suffix.lower() == ".md" else []

    md_files: list[Path] = []
    for path in sorted(target.rglob("*.md")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        md_files.append(path)
    return md_files


def lint_file(
    file_path: Path,
    config: DocsCIConfig,
    rules: list[BaseRule],
) -> list[Violation]:
    """Execute all active rules on a single markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.error("Failed to read file %s: %s", file_path, exc)
            return []
    except Exception as exc:
        logger.error("Failed to read file %s: %s", file_path, exc)
        return []

    front_matter, body, _ = parse_front_matter(content)
    lines = content.splitlines()

    context = RuleContext(
        file_path=file_path,
        raw_content=content,
        front_matter=front_matter,
        body=body,
        lines=lines,
        config=config,
        terminology=config.terminology,
    )

    violations: list[Violation] = []
    for rule in rules:
        try:
            rule_violations = rule.run(context)
            violations.extend(rule_violations)
        except Exception as exc:
            logger.exception("Error executing rule %s on %s: %s", rule.id, file_path, exc)

    # Sort violations primarily by file, then by line, then column
    violations.sort(key=lambda v: (str(v.file_path), v.line, v.column))
    return violations


def lint_path(
    target: Path,
    config: DocsCIConfig,
    rules: list[BaseRule] | None = None,
) -> tuple[list[Violation], int]:
    """Lint all markdown files found at target path.

    Returns:
        tuple of (all_violations, scanned_files_count)
    """
    if rules is None:
        rules = RuleRegistry.get_configured_rules(config)

    files = collect_markdown_files(target)
    all_violations: list[Violation] = []

    for file_path in files:
        file_violations = lint_file(file_path, config, rules)
        all_violations.extend(file_violations)

    return all_violations, len(files)
