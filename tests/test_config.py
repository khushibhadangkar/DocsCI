"""Tests for configuration and terminology loaders."""

from __future__ import annotations

from pathlib import Path

from docsci.config import find_default_file, load_config, load_terminology
from docsci.models import Severity, Violation


def test_severity_from_str() -> None:
    assert Severity.from_str("error") == Severity.ERROR
    assert Severity.from_str("WARNING") == Severity.WARNING
    assert Severity.from_str("info") == Severity.INFO
    assert Severity.from_str("unknown") == Severity.WARNING


def test_load_default_config() -> None:
    config = load_config()
    assert config is not None
    assert isinstance(config.rules, dict)
    assert "heading-hierarchy" in config.rules
    assert config.rules["heading-hierarchy"].severity == Severity.ERROR
    assert config.links.timeout_seconds > 0
    assert len(config.terminology) > 0


def test_load_terminology_from_file(tmp_path: Path) -> None:
    term_file = tmp_path / "custom_term.yml"
    term_file.write_text(
        """
terms:
  - preferred: "primary node"
    forbidden:
      - "master node"
      - "leader node"
    explanation: "Use primary node in distributed cluster topics."
"""
    )
    terms = load_terminology(term_file)
    assert len(terms) == 1
    assert terms[0].preferred == "primary node"
    assert "master node" in terms[0].forbidden
    assert "leader node" in terms[0].forbidden
    assert "primary node" in terms[0].explanation


def test_load_config_missing_file(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist.yml"
    config = load_config(non_existent)
    assert config is not None
    assert config.rules == {}


def test_load_config_malformed_yaml(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("rules: [this is: bad: {")
    config = load_config(bad_yaml)
    assert config is not None
    assert config.rules == {}


def test_find_default_file_not_found(tmp_path: Path) -> None:
    found = find_default_file(["non_existent.yml"], search_dir=tmp_path)
    assert found is None


def test_violation_to_dict_and_annotation() -> None:
    v = Violation(
        rule_id="banned-phrases",
        file_path=Path("docs/intro.md"),
        line=10,
        column=4,
        message="Avoid 'simply'",
        severity=Severity.WARNING,
        suggestion="Remove 'simply'",
    )
    d = v.to_dict()
    assert d["rule_id"] == "banned-phrases"
    assert d["line"] == 10
    assert d["severity"] == "warning"

    annot = v.to_github_annotation()
    assert annot.startswith("::warning")
    assert "file=docs/intro.md" in annot
    assert "line=10" in annot
    assert "Avoid 'simply'" in annot
    assert "Suggested fix: Remove 'simply'" in annot


def test_violation_error_annotation() -> None:
    v = Violation(
        rule_id="single-h1",
        file_path=Path("docs/page.md"),
        line=1,
        column=1,
        message="Multiple H1 headings",
        severity=Severity.ERROR,
    )
    annot = v.to_github_annotation()
    assert annot.startswith("::error")
