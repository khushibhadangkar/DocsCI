"""Unit tests for conventional commits release notes generator."""

from __future__ import annotations

from pathlib import Path

import git
import pytest
from typer.testing import CliRunner

from docsci.cli import app
from docsci.config import load_config
from docsci.linter import lint_file
from docsci.models import CommitEntry, ReleaseNotesConfig, Severity
from docsci.release_notes import (
    extract_commits,
    generate_release_notes_markdown,
    parse_conventional_commit,
)
from docsci.rules import RuleRegistry

runner = CliRunner()


def test_parse_conventional_commit_feat() -> None:
    entry = parse_conventional_commit(
        commit_hash="abc1234567890",
        author="Alice",
        date_str="2026-11-04",
        message="feat(storage): support AWS S3 immutable retention (#101)",
    )
    assert entry.short_hash == "abc1234"
    assert entry.type == "feat"
    assert entry.scope == "storage"
    assert entry.pr == "101"
    assert "Support AWS S3 immutable retention" in entry.description
    assert not entry.breaking


def test_parse_conventional_commit_breaking() -> None:
    entry = parse_conventional_commit(
        commit_hash="def9876543210",
        author="Bob",
        date_str="2026-11-04",
        message="feat(api)!: drop legacy v1 authentication endpoints\n\nBREAKING CHANGE: v1 auth removed",
    )
    assert entry.breaking is True
    assert entry.type == "feat"
    assert entry.scope == "api"


def test_parse_conventional_commit_fallback() -> None:
    entry = parse_conventional_commit(
        commit_hash="111222333444",
        author="Charlie",
        date_str="2026-11-04",
        message="misc non-conventional update to readme",
    )
    assert entry.type == "chore"
    assert entry.description == "Misc non-conventional update to readme"


def test_generate_release_notes_lint_clean(tmp_path: Path) -> None:
    commits = [
        CommitEntry(
            hash="1a2b3c4d5e6f",
            short_hash="1a2b3c4",
            author="Dev",
            date="2026-11-04",
            type="feat",
            scope="backup",
            description="Add support for scheduled backup jobs",
            breaking=False,
            pr="12",
        ),
        CommitEntry(
            hash="2b3c4d5e6f7a",
            short_hash="2b3c4d5",
            author="Dev",
            date="2026-11-04",
            type="fix",
            scope="network",
            description="Resolve connection timeout on slow links",
            breaking=False,
            pr="15",
        ),
    ]

    cfg = ReleaseNotesConfig()
    md = generate_release_notes_markdown(commits, target_version="v2.1.0", config=cfg)
    assert "---" in md
    assert "title: Release notes for version 2.1.0" in md
    assert "## 🚀 Added" in md
    assert "## 🐛 Fixed" in md
    assert "1a2b3c4" in md

    # Write to file and lint it: MUST BE LINT-CLEAN
    doc_file = tmp_path / "RELEASE_NOTES.md"
    doc_file.write_text(md, encoding="utf-8")

    docsci_cfg = load_config()
    rules = RuleRegistry.get_configured_rules(docsci_cfg)
    violations = lint_file(doc_file, docsci_cfg, rules)
    errors = [v for v in violations if v.severity == Severity.ERROR]
    assert len(errors) == 0, f"Generated release notes produced errors: {[e.to_dict() for e in errors]}"


def test_generate_release_notes_empty_commits() -> None:
    md = generate_release_notes_markdown([], target_version="v1.0.0")
    assert "No changes recorded for this release range." in md


@pytest.fixture
def git_fixture_repo(tmp_path: Path) -> Path:
    """Create a temporary Git repository with conventional commits and tags."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    repo = git.Repo.init(repo_dir)

    # Configure committer
    repo.config_writer().set_value("user", "name", "Test Committer").release()
    repo.config_writer().set_value("user", "email", "committer@example.com").release()

    # Commit 1
    f1 = repo_dir / "file1.txt"
    f1.write_text("initial")
    repo.index.add([str(f1)])
    c1 = repo.index.commit("chore: initial commit")
    repo.create_tag("v1.0.0", ref=c1)

    # Commit 2
    f2 = repo_dir / "file2.txt"
    f2.write_text("feature")
    repo.index.add([str(f2)])
    repo.index.commit("feat(vault): add immutable vault encryption (#22)")

    # Commit 3
    f3 = repo_dir / "file3.txt"
    f3.write_text("fix")
    repo.index.add([str(f3)])
    c3 = repo.index.commit("fix(restore): prevent file overwrite during recovery")
    repo.create_tag("v1.1.0", ref=c3)

    return repo_dir


def test_extract_commits_from_git_repo(git_fixture_repo: Path) -> None:
    commits = extract_commits(git_fixture_repo, from_tag="v1.0.0", to_tag="v1.1.0")
    assert len(commits) == 2
    types = [c.type for c in commits]
    assert "feat" in types
    assert "fix" in types


def test_cli_release_notes(git_fixture_repo: Path, tmp_path: Path) -> None:
    out_file = tmp_path / "output_release_notes.md"
    result = runner.invoke(
        app,
        [
            "release-notes",
            "--repo",
            str(git_fixture_repo),
            "--from",
            "v1.0.0",
            "--to",
            "v1.1.0",
            "--output",
            str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "immutable vault encryption" in content.lower()
    assert "prevent file overwrite" in content.lower()
