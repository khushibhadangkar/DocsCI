"""Data models and enums for DocsCI."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Severity(StrEnum):
    """Severity levels for linting violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @classmethod
    def from_str(cls, val: str) -> Severity:
        """Parse severity string case-insensitively."""
        normalized = val.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.WARNING


@dataclass(frozen=True)
class Violation:
    """Represents a single rule violation in a documentation file."""

    rule_id: str
    file_path: Path
    line: int
    column: int
    message: str
    severity: Severity = Severity.WARNING
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert violation to a serializable dictionary."""
        return {
            "rule_id": self.rule_id,
            "file": str(self.file_path),
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
        }

    def to_github_annotation(self) -> str:
        """Format as a GitHub Actions workflow command annotation."""
        # e.g. ::error file=path,line=1,col=1,title=rule_id::message (suggestion: ...)
        sev = "error" if self.severity == Severity.ERROR else "warning"
        msg = self.message
        if self.suggestion:
            msg += f" (Suggested fix: {self.suggestion})"
        return (
            f"::{sev} file={self.file_path},line={self.line},col={self.column},"
            f"title={self.rule_id}::{msg}"
        )


@dataclass
class TermDefinition:
    """Represents a terminology entry with preferred and forbidden terms."""

    preferred: str
    forbidden: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class RuleConfig:
    """Configuration for an individual rule."""

    enabled: bool = True
    severity: Severity = Severity.WARNING
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkConfig:
    """Configuration for link checking."""

    timeout_seconds: float = 5.0
    retries: int = 2
    slow_threshold_seconds: float = 2.0
    rate_limit_delay_seconds: float = 0.1
    allowlist: list[str] = field(default_factory=list)


@dataclass
class ReleaseNotesConfig:
    """Configuration for release notes generation."""

    prompt_path: str = "prompts/release_summary_v1.md"
    output_draft: str = "RELEASE_NOTES_DRAFT.md"
    categories: dict[str, str] = field(
        default_factory=lambda: {
            "breaking": "💥 Breaking Changes",
            "feat": "🚀 Added",
            "fix": "🐛 Fixed",
            "perf": "⚡ Performance Improvements",
            "docs": "📝 Documentation",
        }
    )


@dataclass
class DocsCIConfig:
    """Top-level DocsCI configuration object."""

    rules: dict[str, RuleConfig] = field(default_factory=dict)
    links: LinkConfig = field(default_factory=LinkConfig)
    release_notes: ReleaseNotesConfig = field(default_factory=ReleaseNotesConfig)
    terminology: list[TermDefinition] = field(default_factory=list)


@dataclass
class RuleContext:
    """Context passed to each rule during document linting."""

    file_path: Path
    raw_content: str
    front_matter: dict[str, Any]
    body: str
    lines: list[str]
    config: DocsCIConfig
    terminology: list[TermDefinition]


class LinkStatus(StrEnum):
    """Status classification for checked links."""

    OK = "ok"
    REDIRECTED = "redirected"
    SLOW = "slow"
    BROKEN = "broken"
    SKIPPED = "skipped"


@dataclass
class LinkResult:
    """Result of checking a single hyperlink."""

    file_path: Path
    line: int
    url: str
    is_external: bool
    status: LinkStatus
    status_code: int | None = None
    elapsed_seconds: float = 0.0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert link result to dictionary."""
        return {
            "file": str(self.file_path),
            "line": self.line,
            "url": self.url,
            "is_external": self.is_external,
            "status": self.status.value,
            "status_code": self.status_code,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "message": self.message,
        }


@dataclass
class CommitEntry:
    """Parsed conventional commit entry."""

    hash: str
    short_hash: str
    author: str
    date: str
    type: str
    scope: str | None
    description: str
    body: str = ""
    breaking: bool = False
    pr: str | None = None

    def display_line(self) -> str:
        """Format entry for release notes."""
        scope_prefix = f"**{self.scope}:** " if self.scope else ""
        pr_suffix = f" (#{self.pr})" if self.pr else ""
        return f"- {scope_prefix}{self.description}{pr_suffix} (`{self.short_hash}`)"


@dataclass
class ClaimVerification:
    """Result of verifying an individual AI-generated claim against commits."""

    claim_id: int
    claim_text: str
    status: str  # "SUPPORTED" or "UNSUPPORTED"
    evidence_hashes: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert claim verification to dictionary."""
        return {
            "id": self.claim_id,
            "claim": self.claim_text,
            "status": self.status,
            "evidence": self.evidence_hashes,
            "notes": self.notes,
        }
