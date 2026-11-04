"""Tests for DocsCI command-line interface."""

from __future__ import annotations

from typer.testing import CliRunner

from docsci import __version__
from docsci.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Docs-as-code quality" in result.output
    assert "lint" in result.output
    assert "links" in result.output
    assert "release-notes" in result.output
    assert "report" in result.output


def test_cli_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"docsci version {__version__}" in result.output


def test_cli_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"docsci version {__version__}" in result.output


def test_cli_lint_help() -> None:
    result = runner.invoke(app, ["lint", "--help"])
    assert result.exit_code == 0
    assert "--strict" in result.output
    assert "--format" in result.output


def test_cli_links_help() -> None:
    result = runner.invoke(app, ["links", "--help"])
    assert result.exit_code == 0
    assert "--strict" in result.output


def test_cli_release_notes_help() -> None:
    result = runner.invoke(app, ["release-notes", "--help"])
    assert result.exit_code == 0
    assert "--ai-summary" in result.output
    assert "--allow-unsupported" in result.output


def test_cli_report_help() -> None:
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "--previous" in result.output
