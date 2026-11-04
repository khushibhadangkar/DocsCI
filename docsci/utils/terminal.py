"""Terminal output formatting and GitHub Actions reporter utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docsci.models import Severity, Violation

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
WHITE = "\033[37m"


def format_table_report(
    violations: list[Violation],
    scanned_files_count: int,
    base_dir: Path | None = None,
) -> str:
    """Render a human-readable ANSI table of violations and summary statistics."""
    lines: list[str] = []
    lines.append("")
    lines.append(f"{BOLD}DocsCI Documentation Linting Report{RESET}")
    lines.append("=" * 80)

    if not violations:
        lines.append(
            f"{GREEN}✔ All {scanned_files_count} file(s) passed all style, terminology, "
            f"and metadata rules with 0 violations.{RESET}"
        )
        lines.append("")
        return "\n".join(lines)

    # Group by file
    files_map: dict[str, list[Violation]] = {}
    for v in violations:
        display_path = str(v.file_path)
        if base_dir:
            try:
                display_path = str(v.file_path.relative_to(base_dir))
            except ValueError:
                display_path = str(v.file_path)
        files_map.setdefault(display_path, []).append(v)

    error_count = sum(1 for v in violations if v.severity == Severity.ERROR)
    warning_count = sum(1 for v in violations if v.severity == Severity.WARNING)
    info_count = sum(1 for v in violations if v.severity == Severity.INFO)

    for file_str, file_violations in files_map.items():
        lines.append(f"\n{BOLD}{CYAN}📄 {file_str}{RESET} ({len(file_violations)} violation(s)):")
        for v in file_violations:
            if v.severity == Severity.ERROR:
                sev_badge = f"{RED}[ERROR]{RESET}"
            elif v.severity == Severity.WARNING:
                sev_badge = f"{YELLOW}[WARN ]{RESET}"
            else:
                sev_badge = f"{WHITE}[INFO ]{RESET}"

            loc = f"L{v.line}:{v.column}".ljust(8)
            rule_badge = f"{DIM}({v.rule_id}){RESET}"
            lines.append(f"  {sev_badge} {loc} {v.message} {rule_badge}")
            if v.suggestion:
                lines.append(f"          {DIM}↳ Fix: {v.suggestion}{RESET}")

    lines.append("")
    lines.append("-" * 80)
    summary_text = (
        f"{BOLD}Summary:{RESET} Scanned {scanned_files_count} file(s) | "
        f"{RED}{error_count} error(s){RESET} | "
        f"{YELLOW}{warning_count} warning(s){RESET} | "
        f"{info_count} info"
    )
    lines.append(summary_text)
    lines.append("")
    return "\n".join(lines)


def format_json_report(
    violations: list[Violation],
    scanned_files_count: int,
) -> str:
    """Format violations as structured JSON string."""
    error_count = sum(1 for v in violations if v.severity == Severity.ERROR)
    warning_count = sum(1 for v in violations if v.severity == Severity.WARNING)
    info_count = sum(1 for v in violations if v.severity == Severity.INFO)

    report_data: dict[str, Any] = {
        "summary": {
            "scanned_files": scanned_files_count,
            "total_violations": len(violations),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
        },
        "violations": [v.to_dict() for v in violations],
    }
    return json.dumps(report_data, indent=2)


def format_github_annotations(
    violations: list[Violation],
    scanned_files_count: int,
) -> str:
    """Format violations as GitHub Actions annotation commands."""
    lines: list[str] = [v.to_github_annotation() for v in violations]
    lines.append(
        f"::notice::DocsCI scanned {scanned_files_count} files: "
        f"{sum(1 for v in violations if v.severity == Severity.ERROR)} errors, "
        f"{sum(1 for v in violations if v.severity == Severity.WARNING)} warnings."
    )
    return "\n".join(lines)
