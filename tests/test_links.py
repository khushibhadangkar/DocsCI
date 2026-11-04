"""Unit tests for DocsCI link checker."""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from docsci.cli import app
from docsci.link_checker import (
    LinkChecker,
    format_link_github_annotations,
    format_link_json_report,
    format_link_table_report,
)
from docsci.models import LinkConfig, LinkResult, LinkStatus

runner = CliRunner()


def test_internal_links_valid(tmp_path: Path) -> None:
    doc1 = tmp_path / "doc1.md"
    doc2 = tmp_path / "doc2.md"

    doc2.write_text("# Target Document\n\n## Sub Heading\n\nTarget content.")
    doc1.write_text(
        "# Source Document\n\n"
        "[Link to doc2](doc2.md)\n"
        "[Link to doc2 heading](doc2.md#sub-heading)\n"
        "[Link to own heading](#source-document)\n"
    )

    checker = LinkChecker(config=LinkConfig())
    results, count = checker.check_path(doc1)
    assert count == 1
    assert len(results) == 3
    assert all(r.status == LinkStatus.OK for r in results)


def test_internal_links_broken_file(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# Doc\n\n[Missing](missing_file.md)")

    checker = LinkChecker()
    results = checker.check_file(doc)
    assert len(results) == 1
    assert results[0].status == LinkStatus.BROKEN
    assert "does not exist" in results[0].message


def test_internal_links_broken_anchor(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# Main Topic\n\n[Bad Anchor](#does-not-exist)")

    checker = LinkChecker()
    results = checker.check_file(doc)
    assert len(results) == 1
    assert results[0].status == LinkStatus.BROKEN
    assert "not found in document" in results[0].message


def test_internal_links_broken_anchor_in_other_file(tmp_path: Path) -> None:
    doc1 = tmp_path / "doc1.md"
    doc2 = tmp_path / "doc2.md"

    doc2.write_text("# Other Doc\n\n## Section Exists")
    doc1.write_text("[Bad Remote Anchor](doc2.md#section-missing)")

    checker = LinkChecker()
    results = checker.check_file(doc1)
    assert len(results) == 1
    assert results[0].status == LinkStatus.BROKEN
    assert "not found in 'doc2.md'" in results[0].message


def test_allowlisted_url(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("[Example](https://example.com/test)")

    cfg = LinkConfig(allowlist=["https://example.com"])
    checker = LinkChecker(config=cfg)
    results = checker.check_file(doc)
    assert len(results) == 1
    assert results[0].status == LinkStatus.OK
    assert "Allowlisted" in results[0].message


def test_skipped_protocol(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("Contact [Us](mailto:support@example.com) or [Call](tel:12345)")

    checker = LinkChecker()
    results = checker.check_file(doc)
    assert len(results) == 2
    assert all(r.status == LinkStatus.SKIPPED for r in results)


@patch("urllib.request.urlopen")
def test_external_link_success_and_cache(mock_urlopen: MagicMock, tmp_path: Path) -> None:
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    doc = tmp_path / "doc.md"
    doc.write_text(
        "[API Doc](https://api.mycorp.internal/v1)\n"
        "[Duplicate API Doc](https://api.mycorp.internal/v1)\n"
    )

    cfg = LinkConfig(rate_limit_delay_seconds=0.0)
    checker = LinkChecker(config=cfg)
    results = checker.check_file(doc)

    assert len(results) == 2
    assert results[0].status == LinkStatus.OK
    assert results[1].status == LinkStatus.OK
    assert "cached" in results[1].message
    # Cached call should only hit urlopen once
    assert mock_urlopen.call_count == 1


@patch("urllib.request.urlopen")
def test_external_link_slow(mock_urlopen: MagicMock, tmp_path: Path) -> None:
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    # Simulate slow response
    def slow_urlopen(*args, **kwargs):
        import time
        time.sleep(0.05)
        return mock_resp

    mock_urlopen.side_effect = slow_urlopen

    doc = tmp_path / "doc.md"
    doc.write_text("[Slow Service](https://slow.mycorp.internal)")

    cfg = LinkConfig(rate_limit_delay_seconds=0.0, slow_threshold_seconds=0.01)
    checker = LinkChecker(config=cfg)
    results = checker.check_file(doc)
    assert len(results) == 1
    assert results[0].status == LinkStatus.SLOW


@patch("urllib.request.urlopen")
def test_external_link_redirected(mock_urlopen: MagicMock, tmp_path: Path) -> None:
    headers = {"Location": "https://new.mycorp.internal"}
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://old.mycorp.internal",
        code=301,
        msg="Moved Permanently",
        hdrs=headers,
        fp=None,
    )

    doc = tmp_path / "doc.md"
    doc.write_text("[Old URL](https://old.mycorp.internal)")

    cfg = LinkConfig(rate_limit_delay_seconds=0.0)
    checker = LinkChecker(config=cfg)
    results = checker.check_file(doc)
    assert len(results) == 1
    assert results[0].status == LinkStatus.REDIRECTED
    assert "Redirected to https://new.mycorp.internal" in results[0].message


@patch("urllib.request.urlopen")
def test_external_link_broken_http_error(mock_urlopen: MagicMock, tmp_path: Path) -> None:
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://bad.mycorp.internal/404",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=None,
    )

    doc = tmp_path / "doc.md"
    doc.write_text("[Bad Link](https://bad.mycorp.internal/404)")

    cfg = LinkConfig(retries=0, rate_limit_delay_seconds=0.0)
    checker = LinkChecker(config=cfg)
    results = checker.check_file(doc)
    assert len(results) == 1
    assert results[0].status == LinkStatus.BROKEN
    assert "HTTP 404" in results[0].message


def test_format_link_reports() -> None:
    results = [
        LinkResult(
            file_path=Path("docs/intro.md"),
            line=5,
            url="https://broken.example.com",
            is_external=True,
            status=LinkStatus.BROKEN,
            status_code=404,
            message="HTTP 404 Not Found",
        ),
        LinkResult(
            file_path=Path("docs/intro.md"),
            line=8,
            url="https://slow.example.com",
            is_external=True,
            status=LinkStatus.SLOW,
            status_code=200,
            elapsed_seconds=2.5,
            message="Slow response (2.5s)",
        ),
    ]

    table_report = format_link_table_report(results, 1)
    assert "DocsCI Link Integrity Report" in table_report
    assert "broken.example.com" in table_report
    assert "[BROKEN  ]" in table_report
    assert "[SLOW    ]" in table_report

    json_report = format_link_json_report(results, 1)
    parsed = json.loads(json_report)
    assert parsed["summary"]["broken"] == 1
    assert parsed["summary"]["slow"] == 1

    gh_report = format_link_github_annotations(results, 1)
    assert "::error file=docs/intro.md" in gh_report
    assert "::warning file=docs/intro.md" in gh_report


def test_cli_links_ok(tmp_path: Path) -> None:
    doc = tmp_path / "clean.md"
    doc.write_text("# Clean\n\n## Section\n\n[Local Section](#section)")
    result = runner.invoke(app, ["links", str(doc)])
    assert result.exit_code == 0
    assert "valid and healthy" in result.output


def test_cli_links_broken(tmp_path: Path) -> None:
    doc = tmp_path / "broken.md"
    doc.write_text("# Broken\n\n[Missing](non_existent_file.md)")
    result = runner.invoke(app, ["links", str(doc)])
    assert result.exit_code == 1
    assert "BROKEN" in result.output


def test_cli_links_strict_with_slow(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# Doc\n\n[Link](other.md)")
    (tmp_path / "other.md").write_text("# Other")

    # When all links are OK, strict exits 0
    result_ok = runner.invoke(app, ["links", str(doc), "--strict"])
    assert result_ok.exit_code == 0


def test_cli_links_nonexistent_path() -> None:
    result = runner.invoke(app, ["links", "path_does_not_exist_xyz.md"])
    assert result.exit_code == 2
    assert "does not exist" in result.output
