"""Configuration loader and schema validator for DocsCI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from docsci.models import (
    DocsCIConfig,
    LinkConfig,
    ReleaseNotesConfig,
    RuleConfig,
    Severity,
    TermDefinition,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILENAMES = ["docsci.yml", "docsci.yaml", ".docsci.yml", ".docsci.yaml"]
DEFAULT_TERMINOLOGY_FILENAMES = ["terminology.yml", "terminology.yaml"]


def find_default_file(candidates: list[str], search_dir: Path | None = None) -> Path | None:
    """Find the first matching candidate file in search_dir or current directory."""
    base = search_dir or Path.cwd()
    for name in candidates:
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def load_terminology(path: Path | None = None) -> list[TermDefinition]:
    """Load terminology definitions from a YAML file."""
    if path is None:
        path = find_default_file(DEFAULT_TERMINOLOGY_FILENAMES)

    if path is None or not path.is_file():
        return []

    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
    except Exception as exc:
        logger.warning("Failed to load terminology file %s: %s", path, exc)
        return []

    terms: list[TermDefinition] = []
    raw_terms = data.get("terms", [])
    if isinstance(raw_terms, list):
        for item in raw_terms:
            if not isinstance(item, dict):
                continue
            preferred = str(item.get("preferred", "")).strip()
            if not preferred:
                continue
            forbidden_raw = item.get("forbidden", [])
            forbidden: list[str] = []
            if isinstance(forbidden_raw, list):
                forbidden = [str(f).strip() for f in forbidden_raw if str(f).strip()]
            explanation = str(item.get("explanation", "")).strip()
            terms.append(
                TermDefinition(
                    preferred=preferred,
                    forbidden=forbidden,
                    explanation=explanation,
                )
            )

    return terms


def load_config(
    config_path: Path | None = None,
    terminology_path: Path | None = None,
) -> DocsCIConfig:
    """Load DocsCI configuration from YAML file and merge with terminology."""
    if config_path is None:
        config_path = find_default_file(DEFAULT_CONFIG_FILENAMES)

    config = DocsCIConfig()

    data: dict[str, Any] = {}
    if config_path and config_path.is_file():
        try:
            content = config_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content) or {}
        except Exception as exc:
            logger.warning("Failed to parse config file %s: %s", config_path, exc)

    # Parse rules
    rules_dict: dict[str, RuleConfig] = {}
    raw_rules = data.get("rules", {})
    if isinstance(raw_rules, dict):
        for rule_id, rule_data in raw_rules.items():
            if not isinstance(rule_data, dict):
                continue
            enabled = bool(rule_data.get("enabled", True))
            severity_str = str(rule_data.get("severity", "warning"))
            severity = Severity.from_str(severity_str)
            options = {k: v for k, v in rule_data.items() if k not in ("enabled", "severity")}
            rules_dict[str(rule_id)] = RuleConfig(
                enabled=enabled,
                severity=severity,
                options=options,
            )
    config.rules = rules_dict

    # Parse links config
    raw_links = data.get("links", {})
    if isinstance(raw_links, dict):
        config.links = LinkConfig(
            timeout_seconds=float(raw_links.get("timeout_seconds", 5.0)),
            retries=int(raw_links.get("retries", 2)),
            slow_threshold_seconds=float(raw_links.get("slow_threshold_seconds", 2.0)),
            rate_limit_delay_seconds=float(raw_links.get("rate_limit_delay_seconds", 0.1)),
            allowlist=list(raw_links.get("allowlist", [])),
        )

    # Parse release notes config
    raw_release_notes = data.get("release_notes", {})
    if isinstance(raw_release_notes, dict):
        categories = raw_release_notes.get("categories")
        if not isinstance(categories, dict):
            categories = {
                "breaking": "💥 Breaking Changes",
                "feat": "🚀 Added",
                "fix": "🐛 Fixed",
                "perf": "⚡ Performance Improvements",
                "docs": "📝 Documentation",
            }
        config.release_notes = ReleaseNotesConfig(
            prompt_path=str(
                raw_release_notes.get("prompt_path", "prompts/release_summary_v1.md")
            ),
            output_draft=str(raw_release_notes.get("output_draft", "RELEASE_NOTES_DRAFT.md")),
            categories=categories,
        )

    # Load terminology (check rule options first if defined)
    term_file = terminology_path
    if term_file is None:
        term_rule_cfg = config.rules.get("terminology-preferred")
        if term_rule_cfg and "file" in term_rule_cfg.options:
            term_file = Path(str(term_rule_cfg.options["file"]))

    config.terminology = load_terminology(term_file)
    return config
