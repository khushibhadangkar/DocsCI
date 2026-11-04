"""Conventional Commits release notes generator producing lint-compliant Markdown."""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path

from docsci.models import CommitEntry, ReleaseNotesConfig

logger = logging.getLogger(__name__)

CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)
PR_PATTERN = re.compile(r"\(#(?P<pr>\d+)\)|#(?P<pr_alt>\d+)")


def parse_conventional_commit(
    commit_hash: str,
    author: str,
    date_str: str,
    message: str,
) -> CommitEntry:
    """Parse a Git commit message following the Conventional Commits specification."""
    lines = [ln.strip() for ln in message.strip().splitlines() if ln.strip()]
    first_line = lines[0] if lines else ""
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""

    short_hash = commit_hash[:7] if len(commit_hash) >= 7 else commit_hash
    pr_number: str | None = None
    pr_match = PR_PATTERN.search(first_line)
    if pr_match:
        pr_number = pr_match.group("pr") or pr_match.group("pr_alt")

    match = CONVENTIONAL_PATTERN.match(first_line)
    if match:
        c_type = match.group("type").lower()
        scope = match.group("scope")
        desc = match.group("desc").strip()
        breaking = bool(match.group("breaking")) or "BREAKING CHANGE:" in message or "BREAKING-CHANGE:" in message
    else:
        # Fallback for non-conventional commit messages
        c_type = "chore"
        scope = None
        desc = first_line
        breaking = "BREAKING CHANGE:" in message

    # Clean description: strip trailing PR pattern and capitalize first letter for lint elegance
    if desc:
        desc = PR_PATTERN.sub("", desc).strip()
        desc = desc[0].upper() + desc[1:] if desc else ""

    return CommitEntry(
        hash=commit_hash,
        short_hash=short_hash,
        author=author,
        date=date_str,
        type=c_type,
        scope=scope,
        description=desc,
        body=body,
        breaking=breaking,
        pr=pr_number,
    )


def extract_commits(
    repo_path: Path,
    from_tag: str | None = None,
    to_tag: str = "HEAD",
) -> list[CommitEntry]:
    """Extract commits from Git repository between from_tag and to_tag."""
    try:
        import git
    except ImportError:
        logger.error("GitPython is required for release notes generation.")
        return []

    try:
        repo = git.Repo(str(repo_path), search_parent_directories=True)
    except Exception as exc:
        logger.error("Could not open Git repository at %s: %s", repo_path, exc)
        return []

    # Resolve revision range
    if from_tag:
        rev_range = f"{from_tag}..{to_tag}"
    else:
        # If no from_tag specified, check if there's a previous tag
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime if hasattr(t, "commit") else 0)
        if tags:
            prev_tag = tags[-1].name
            rev_range = f"{prev_tag}..{to_tag}"
        else:
            rev_range = to_tag

    try:
        commits = list(repo.iter_commits(rev_range))
    except Exception as exc:
        logger.warning("Could not iterate commits in range '%s': %s", rev_range, exc)
        # Try fallback to all commits up to to_tag
        try:
            commits = list(repo.iter_commits(to_tag))
        except Exception:
            return []

    parsed_entries: list[CommitEntry] = []
    for c in reversed(commits):  # Chronological order
        date_str = date.fromtimestamp(c.committed_date).isoformat()
        author = str(c.author.name) if c.author else "Unknown"
        entry = parse_conventional_commit(
            commit_hash=c.hexsha,
            author=author,
            date_str=date_str,
            message=c.message,
        )
        parsed_entries.append(entry)

    return parsed_entries


def generate_release_notes_markdown(
    commits: list[CommitEntry],
    target_version: str = "v1.0.0",
    config: ReleaseNotesConfig | None = None,
) -> str:
    """Produce lint-clean Markdown release notes with valid YAML front matter."""
    cfg = config or ReleaseNotesConfig()
    today_str = date.today().isoformat()
    clean_version = target_version.lstrip("v")

    # Front matter
    lines: list[str] = [
        "---",
        f"title: Release notes for version {clean_version}",
        f"description: New features, improvements, and fixes in release version {clean_version}",
        f"product_version: '{clean_version}'",
        f"last_reviewed: '{today_str}'",
        "owner: docs-team",
        "---",
        "",
        f"# Release notes for version {clean_version}",
        "",
        f"Welcome to the release notes for version {clean_version}. "
        "Review the sections below for details on changes, additions, and resolved issues.",
        "",
    ]

    if not commits:
        lines.append("No changes recorded for this release range.\n")
        return "\n".join(lines)

    # Group commits into categories
    breaking_commits: list[CommitEntry] = [c for c in commits if c.breaking]
    added_commits: list[CommitEntry] = [c for c in commits if not c.breaking and c.type == "feat"]
    fixed_commits: list[CommitEntry] = [c for c in commits if not c.breaking and c.type == "fix"]
    perf_commits: list[CommitEntry] = [c for c in commits if not c.breaking and c.type in ("perf", "refactor")]
    doc_commits: list[CommitEntry] = [c for c in commits if not c.breaking and c.type == "docs"]

    groups = [
        (cfg.categories.get("breaking", "💥 Breaking Changes"), breaking_commits),
        (cfg.categories.get("feat", "🚀 Added"), added_commits),
        (cfg.categories.get("fix", "🐛 Fixed"), fixed_commits),
        (cfg.categories.get("perf", "⚡ Performance Improvements"), perf_commits),
        (cfg.categories.get("docs", "📝 Documentation"), doc_commits),
    ]

    for title, group_commits in groups:
        if not group_commits:
            continue
        lines.append(f"## {title}")
        lines.append("")
        for c in group_commits:
            lines.append(c.display_line())
        lines.append("")

    return "\n".join(lines)
