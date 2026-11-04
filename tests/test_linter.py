"""Unit tests for the linter engine, file scanning, and output reporters."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from docsci.cli import app
from docsci.config import load_config
from docsci.linter import collect_markdown_files, lint_file
from docsci.models import Severity, Violation
from docsci.rules import RuleRegistry
from docsci.utils.markdown_parser import (
    mask_fenced_code,
    mask_inline_code,
    parse_front_matter,
    slugify_heading,
)
from docsci.utils.terminal import (
    format_github_annotations,
    format_json_report,
    format_table_report,
)

runner = CliRunner()


def test_markdown_parser_front_matter() -> None:
    content = "---\ntitle: Sample\ndescription: Desc\n---\n# Body"
    fm, body, lines = parse_front_matter(content)
    assert fm["title"] == "Sample"
    assert fm["description"] == "Desc"
    assert body.strip() == "# Body"
    assert lines == 4


def test_markdown_parser_malformed_front_matter() -> None:
    content = "---\n: bad yaml: [[\n---\n# Body"
    fm, body, lines = parse_front_matter(content)
    assert fm.get("_malformed") is True
    assert body.strip() == "# Body"


def test_markdown_parser_no_front_matter() -> None:
    content = "# Just Body"
    fm, body, lines = parse_front_matter(content)
    assert fm == {}
    assert body == content
    assert lines == 0


def test_mask_fenced_code() -> None:
    content = "Line 1\n```bash\nsimply do this\n```\nLine 5"
    masked = mask_fenced_code(content)
    assert "simply do this" not in masked
    assert masked.splitlines()[0] == "Line 1"
    assert masked.splitlines()[-1] == "Line 5"


def test_mask_inline_code() -> None:
    line = "Use `simply` as code."
    masked = mask_inline_code(line)
    assert "`simply`" not in masked
    assert len(masked) == len(line)


def test_slugify_heading() -> None:
    assert slugify_heading("Configure S3 Storage!") == "configure-s3-storage"
    assert slugify_heading("What is `docsci`?") == "what-is-docsci"
    assert slugify_heading("[Link Title](https://example.com)") == "link-title"


def test_collect_markdown_files(tmp_path: Path) -> None:
    doc1 = tmp_path / "doc1.md"
    doc1.write_text("# Doc 1")
    sub = tmp_path / "sub"
    sub.mkdir()
    doc2 = sub / "doc2.md"
    doc2.write_text("# Doc 2")
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.md").write_text("# Ignored")

    collected = collect_markdown_files(tmp_path)
    assert doc1 in collected
    assert doc2 in collected
    assert (ignored_dir / "ignored.md") not in collected


def test_lint_file_empty(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("")
    config = load_config()
    rules = RuleRegistry.get_configured_rules(config)
    violations = lint_file(empty_file, config, rules)
    # Empty file has missing front matter
    assert any(v.rule_id == "front-matter-required" for v in violations)


def test_lint_file_unicode(tmp_path: Path) -> None:
    unicode_file = tmp_path / "unicode.md"
    unicode_file.write_text(
        "---\ntitle: Resumé & Über-Configuration 🚀\ndescription: UTF-8 doc\n"
        "product_version: '1.0'\nlast_reviewed: '2026-11-04'\nowner: docs\n---\n"
        "# Resumé and system overview\n\nAll systems operational.\n",
        encoding="utf-8",
    )
    config = load_config()
    rules = RuleRegistry.get_configured_rules(config)
    violations = lint_file(unicode_file, config, rules)
    # Filter for errors
    errors = [v for v in violations if v.severity == Severity.ERROR]
    assert len(errors) == 0


def test_format_reports() -> None:
    v = Violation(
        rule_id="banned-phrases",
        file_path=Path("docs/page.md"),
        line=12,
        column=5,
        message="Banned word 'simply'",
        severity=Severity.WARNING,
        suggestion="Remove 'simply'",
    )
    table_out = format_table_report([v], 1)
    assert "DocsCI Documentation Linting Report" in table_out
    assert "page.md" in table_out
    assert "banned-phrases" in table_out

    json_out = format_json_report([v], 1)
    parsed = json.loads(json_out)
    assert parsed["summary"]["warnings"] == 1
    assert parsed["violations"][0]["rule_id"] == "banned-phrases"

    github_out = format_github_annotations([v], 1)
    assert "::warning file=docs/page.md" in github_out
    assert "::notice::" in github_out


def test_format_table_report_zero_violations() -> None:
    table_out = format_table_report([], 5)
    assert "All 5 file(s) passed" in table_out


def test_cli_lint_clean_file(tmp_path: Path) -> None:
    clean_doc = tmp_path / "clean.md"
    clean_doc.write_text(
        "---\ntitle: Clean Document\ndescription: Fully compliant document\n"
        "product_version: '1.0'\nlast_reviewed: '2026-11-04'\nowner: docs\n---\n"
        "# Clean document\n\nTechnical writers write clear docs.\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["lint", str(clean_doc)])
    assert result.exit_code == 0
    assert "All 1 file(s) passed" in result.output


def test_cli_lint_failing_error(tmp_path: Path) -> None:
    bad_doc = tmp_path / "bad.md"
    bad_doc.write_text("# Skipped\n\n### Heading 3 without H2\n")
    result = runner.invoke(app, ["lint", str(bad_doc)])
    assert result.exit_code == 1
    assert "heading-hierarchy" in result.output or "front-matter-required" in result.output


def test_cli_lint_strict_mode(tmp_path: Path) -> None:
    # Has valid front matter and headings, but contains a warning-level banned word ("simply")
    warn_doc = tmp_path / "warn.md"
    warn_doc.write_text(
        "---\ntitle: Warning Document\ndescription: Has banned word\n"
        "product_version: '1.0'\nlast_reviewed: '2026-11-04'\nowner: docs\n---\n"
        "# Warning document\n\nTechnical writers simply explain things.\n",
        encoding="utf-8",
    )
    # Non-strict should pass (exit 0) because there are no ERRORs
    result_lenient = runner.invoke(app, ["lint", str(warn_doc)])
    assert result_lenient.exit_code == 0

    # Strict mode should fail (exit 1) on WARNINGs
    result_strict = runner.invoke(app, ["lint", str(warn_doc), "--strict"])
    assert result_strict.exit_code == 1


def test_cli_lint_nonexistent_path() -> None:
    result = runner.invoke(app, ["lint", "does_not_exist_at_all.md"])
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_cli_lint_json_and_github_formats(tmp_path: Path) -> None:
    doc = tmp_path / "test.md"
    doc.write_text("# Test\n")
    res_json = runner.invoke(app, ["lint", str(doc), "--format", "json"])
    assert res_json.exit_code == 1
    parsed = json.loads(res_json.output)
    assert "violations" in parsed

    res_gh = runner.invoke(app, ["lint", str(doc), "--format", "github"])
    assert res_gh.exit_code == 1
    assert "::error" in res_gh.output or "::warning" in res_gh.output
