"""Command-line interface for DocsCI."""

from __future__ import annotations

from pathlib import Path

import typer

import docsci

app = typer.Typer(
    name="docsci",
    help="Docs-as-code quality, link checking, and release-note automation tool.",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print the version and exit."""
    if value:
        typer.echo(f"docsci version {docsci.__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show DocsCI version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """DocsCI: Quality, links, and release automation for documentation."""


@app.command()
def version() -> None:
    """Display DocsCI version."""
    typer.echo(f"docsci version {docsci.__version__}")


@app.command()
def lint(
    path: Path = typer.Argument(..., help="Path to markdown file or directory of docs to lint."),
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to docsci.yml."),
    terminology: Path | None = typer.Option(
        None, "--terminology", "-t", help="Path to terminology.yml."
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, or github."
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Fail on warnings as well as errors (non-zero exit code)."
    ),
) -> None:
    """Lint Markdown documentation files against style, terminology, and metadata rules."""
    typer.echo(f"Linting {path} (format: {format}, strict: {strict})")


@app.command()
def links(
    path: Path = typer.Argument(..., help="Path to markdown file or directory to check."),
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to docsci.yml."),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, or github."
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Fail on redirected or slow links as well as broken ones."
    ),
) -> None:
    """Check internal anchors and external URLs for broken or slow links."""
    typer.echo(f"Checking links in {path} (format: {format}, strict: {strict})")


@app.command(name="release-notes")
def release_notes(
    from_tag: str | None = typer.Option(None, "--from", help="Starting Git tag or commit hash."),
    to_tag: str | None = typer.Option("HEAD", "--to", help="Target Git tag or commit hash."),
    repo_path: Path = typer.Option(Path("."), "--repo", help="Path to Git repository."),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="File to write release notes to."
    ),
    ai_summary: bool = typer.Option(
        False, "--ai-summary", help="Generate verified AI summary via Gemini API."
    ),
    allow_unsupported: bool = typer.Option(
        False, "--allow-unsupported", help="Do not exit with error if unverified claims exist."
    ),
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to docsci.yml."),
) -> None:
    """Build conventional commit release notes from Git history with optional verified AI summary."""
    typer.echo(
        f"Generating release notes from {from_tag} to {to_tag} "
        f"(ai_summary: {ai_summary}, allow_unsupported: {allow_unsupported})"
    )


@app.command()
def report(
    path: Path = typer.Argument(
        Path("docs"), help="Path to docs directory to generate report for."
    ),
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to docsci.yml."),
    previous: Path | None = typer.Option(
        None, "--previous", "-p", help="Path to previous report JSON for comparison."
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="File to write report to (JSON or MD)."
    ),
) -> None:
    """Generate quality metrics report with before/after comparison."""
    typer.echo(f"Generating report for {path}")


if __name__ == "__main__":
    app()
