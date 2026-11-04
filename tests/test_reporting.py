"""Unit tests for documentation health and before/after comparison reporting."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from docsci.cli import app
from docsci.reporting import compare_reports, format_markdown_report, generate_report_data

runner = CliRunner()


def test_generate_report_data(tmp_path: Path) -> None:
    doc1 = tmp_path / "doc1.md"
    doc1.write_text(
        "---\ntitle: Doc 1\ndescription: Test doc\nproduct_version: '1.0'\n"
        "last_reviewed: '2020-01-01'\nowner: docs\n---\n"
        "# Doc 1\n\nSimply click here [bad link](missing.md).\n"
    )

    data = generate_report_data(tmp_path)
    assert data["scanned_files"] == 1
    assert data["summary"]["total_violations"] >= 1
    assert data["summary"]["broken_links"] == 1
    assert data["summary"]["stale_pages"] >= 1
    assert len(data["top_5_violated_rules"]) >= 1


def test_compare_reports() -> None:
    prev = {
        "timestamp": "2026-10-01T00:00:00",
        "summary": {
            "total_violations": 50,
            "errors": 20,
            "warnings": 30,
            "broken_links": 10,
            "stale_pages": 5,
        },
        "violations_by_rule": {
            "passive-voice": 15,
            "terminology-preferred": 10,
        },
    }

    curr = {
        "timestamp": "2026-11-04T00:00:00",
        "summary": {
            "total_violations": 10,
            "errors": 2,
            "warnings": 8,
            "broken_links": 0,
            "stale_pages": 0,
        },
        "violations_by_rule": {
            "passive-voice": 3,
            "terminology-preferred": 0,
        },
    }

    diff = compare_reports(current=curr, previous=prev)
    assert diff["total_violations"]["previous"] == 50
    assert diff["total_violations"]["current"] == 10
    assert diff["total_violations"]["diff"] == -40
    assert diff["total_violations"]["reduction_percent"] == 80.0
    assert diff["broken_links"]["reduction_percent"] == 100.0


def test_compare_reports_zero_baseline() -> None:
    prev = {"summary": {"total_violations": 0}}
    curr = {"summary": {"total_violations": 5}}
    diff = compare_reports(current=curr, previous=prev)
    assert diff["total_violations"]["reduction_percent"] == -100.0


def test_format_markdown_report_with_comparison() -> None:
    curr_data = {
        "timestamp": "2026-11-04T12:00:00",
        "target_path": "docs",
        "scanned_files": 12,
        "summary": {
            "total_violations": 5,
            "errors": 1,
            "warnings": 4,
            "broken_links": 0,
            "stale_pages": 0,
            "total_links_checked": 25,
        },
        "top_5_violated_rules": [
            {"rule_id": "passive-voice", "severity": "warning", "count": 3}
        ],
        "stale_pages": [],
        "broken_links": [],
    }

    comparison = {
        "previous_timestamp": "2026-10-01",
        "total_violations": {"previous": 25, "current": 5, "diff": -20, "reduction_percent": 80.0},
        "errors": {"previous": 10, "current": 1, "diff": -9, "reduction_percent": 90.0},
        "warnings": {"previous": 15, "current": 4, "diff": -11, "reduction_percent": 73.3},
        "broken_links": {"previous": 4, "current": 0, "diff": -4, "reduction_percent": 100.0},
        "stale_pages": {"previous": 3, "current": 0, "diff": -3, "reduction_percent": 100.0},
        "rule_diffs": [
            {"rule_id": "passive-voice", "previous": 10, "current": 3, "diff": -7, "reduction_percent": 70.0}
        ],
    }

    md = format_markdown_report(curr_data, comparison=comparison)
    assert "# Documentation quality and health report" in md
    assert "Before and after comparison" in md
    assert "80.0% reduction" in md
    assert "Top 5 most violated rules" in md


def test_cli_report_stdout(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Page\n")
    result = runner.invoke(app, ["report", str(tmp_path)])
    assert result.exit_code == 0
    assert "Documentation quality and health report" in result.output


def test_cli_report_output_files(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Page\n")

    out_md = tmp_path / "report.md"
    res_md = runner.invoke(app, ["report", str(tmp_path), "--output", str(out_md)])
    assert res_md.exit_code == 0
    assert out_md.exists()
    assert "# Documentation quality and health report" in out_md.read_text(encoding="utf-8")

    out_json = tmp_path / "report.json"
    res_json = runner.invoke(app, ["report", str(tmp_path), "--output", str(out_json)])
    assert res_json.exit_code == 0
    assert out_json.exists()
    parsed = json.loads(out_json.read_text(encoding="utf-8"))
    assert "report" in parsed


def test_cli_report_with_previous(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Page\n")

    prev_file = tmp_path / "prev.json"
    prev_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-10-01",
                "summary": {"total_violations": 20, "errors": 5, "warnings": 15},
                "violations_by_rule": {"banned-phrases": 10},
            }
        )
    )

    result = runner.invoke(app, ["report", str(tmp_path), "--previous", str(prev_file)])
    assert result.exit_code == 0
    assert "Before and after comparison" in result.output


def test_cli_report_missing_previous() -> None:
    result = runner.invoke(app, ["report", ".", "--previous", "does_not_exist_file.json"])
    assert result.exit_code == 2
    assert "does not exist" in result.output
