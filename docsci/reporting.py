"""Comprehensive documentation health and comparison reporting engine."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from docsci.config import load_config
from docsci.link_checker import LinkChecker
from docsci.linter import lint_path
from docsci.models import DocsCIConfig, LinkStatus, Severity

logger = logging.getLogger(__name__)


def generate_report_data(
    target_path: Path,
    config: DocsCIConfig | None = None,
) -> dict[str, Any]:
    """Execute linting and link checking to assemble raw health metrics."""
    cfg = config or load_config()

    violations, scanned_files_count = lint_path(target_path, cfg)
    checker = LinkChecker(config=cfg.links)
    link_results, _ = checker.check_path(target_path)

    error_count = sum(1 for v in violations if v.severity == Severity.ERROR)
    warning_count = sum(1 for v in violations if v.severity == Severity.WARNING)
    info_count = sum(1 for v in violations if v.severity == Severity.INFO)

    # Group violations by rule
    violations_by_rule: dict[str, int] = {}
    rule_severities: dict[str, str] = {}
    for v in violations:
        violations_by_rule[v.rule_id] = violations_by_rule.get(v.rule_id, 0) + 1
        rule_severities[v.rule_id] = v.severity.value

    # Top 5 most violated rules
    sorted_rules = sorted(violations_by_rule.items(), key=lambda item: item[1], reverse=True)
    top_5 = [
        {
            "rule_id": r_id,
            "count": count,
            "severity": rule_severities.get(r_id, "warning"),
        }
        for r_id, count in sorted_rules[:5]
    ]

    # Stale pages
    stale_violations = [v for v in violations if v.rule_id == "stale-content"]
    stale_pages = [
        {
            "file": str(v.file_path),
            "line": v.line,
            "message": v.message,
        }
        for v in stale_violations
    ]

    # Broken links
    broken_links = [
        {
            "file": str(r.file_path),
            "line": r.line,
            "url": r.url,
            "message": r.message,
        }
        for r in link_results
        if r.status == LinkStatus.BROKEN
    ]

    report = {
        "timestamp": datetime.now().isoformat(),
        "target_path": str(target_path),
        "scanned_files": scanned_files_count,
        "summary": {
            "total_violations": len(violations),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "broken_links": len(broken_links),
            "stale_pages": len(stale_pages),
            "total_links_checked": len(link_results),
        },
        "violations_by_rule": violations_by_rule,
        "top_5_violated_rules": top_5,
        "stale_pages": stale_pages,
        "broken_links": broken_links,
    }

    return report


def compare_reports(
    current: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    """Calculate before/after quality metrics and percentage improvements."""
    prev_summary = previous.get("summary", {})
    curr_summary = current.get("summary", {})

    prev_total = int(prev_summary.get("total_violations", 0))
    curr_total = int(curr_summary.get("total_violations", 0))

    prev_errors = int(prev_summary.get("errors", 0))
    curr_errors = int(curr_summary.get("errors", 0))

    prev_warnings = int(prev_summary.get("warnings", 0))
    curr_warnings = int(curr_summary.get("warnings", 0))

    prev_broken = int(prev_summary.get("broken_links", 0))
    curr_broken = int(curr_summary.get("broken_links", 0))

    prev_stale = int(prev_summary.get("stale_pages", 0))
    curr_stale = int(curr_summary.get("stale_pages", 0))

    def _calc_reduction(prev_val: int, curr_val: int) -> float:
        if prev_val == 0:
            return 0.0 if curr_val == 0 else -100.0
        return round(((prev_val - curr_val) / prev_val) * 100.0, 1)

    # Per rule diffs
    prev_rules = previous.get("violations_by_rule", {})
    curr_rules = current.get("violations_by_rule", {})
    all_rule_keys = sorted(set(prev_rules.keys()).union(set(curr_rules.keys())))

    rule_diffs: list[dict[str, Any]] = []
    for r_id in all_rule_keys:
        p_count = int(prev_rules.get(r_id, 0))
        c_count = int(curr_rules.get(r_id, 0))
        diff = c_count - p_count
        reduction = _calc_reduction(p_count, c_count)
        rule_diffs.append(
            {
                "rule_id": r_id,
                "previous": p_count,
                "current": c_count,
                "diff": diff,
                "reduction_percent": reduction,
            }
        )

    return {
        "previous_timestamp": previous.get("timestamp", "unknown"),
        "current_timestamp": current.get("timestamp", "unknown"),
        "total_violations": {
            "previous": prev_total,
            "current": curr_total,
            "diff": curr_total - prev_total,
            "reduction_percent": _calc_reduction(prev_total, curr_total),
        },
        "errors": {
            "previous": prev_errors,
            "current": curr_errors,
            "diff": curr_errors - prev_errors,
            "reduction_percent": _calc_reduction(prev_errors, curr_errors),
        },
        "warnings": {
            "previous": prev_warnings,
            "current": curr_warnings,
            "diff": curr_warnings - prev_warnings,
            "reduction_percent": _calc_reduction(prev_warnings, curr_warnings),
        },
        "broken_links": {
            "previous": prev_broken,
            "current": curr_broken,
            "diff": curr_broken - prev_broken,
            "reduction_percent": _calc_reduction(prev_broken, curr_broken),
        },
        "stale_pages": {
            "previous": prev_stale,
            "current": curr_stale,
            "diff": curr_stale - prev_stale,
            "reduction_percent": _calc_reduction(prev_stale, curr_stale),
        },
        "rule_diffs": rule_diffs,
    }


def format_markdown_report(
    report_data: dict[str, Any],
    comparison: dict[str, Any] | None = None,
) -> str:
    """Render comprehensive Markdown report including before/after comparison."""
    summary = report_data.get("summary", {})
    lines: list[str] = [
        "# Documentation quality and health report",
        "",
        f"**Generated:** `{report_data.get('timestamp')}` | **Target directory:** `{report_data.get('target_path')}`",
        "",
        "## Overall metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Scanned files | {report_data.get('scanned_files', 0)} |",
        f"| Total violations | {summary.get('total_violations', 0)} |",
        f"| Errors (blocking) | {summary.get('errors', 0)} |",
        f"| Warnings (style/terms) | {summary.get('warnings', 0)} |",
        f"| Broken links | {summary.get('broken_links', 0)} |",
        f"| Stale pages | {summary.get('stale_pages', 0)} |",
        f"| Total hyperlinks verified | {summary.get('total_links_checked', 0)} |",
        "",
    ]

    # Before/After Comparison Table if available
    if comparison:
        tot = comparison["total_violations"]
        err = comparison["errors"]
        warn = comparison["warnings"]
        blk = comparison["broken_links"]
        stl = comparison["stale_pages"]

        lines.extend(
            [
                "## Before and after comparison",
                "",
                f"*Comparing previous scan (`{comparison.get('previous_timestamp')}`) with current scan.*",
                "",
                "| Category | Baseline | Current | Net Change | Quality Improvement |",
                "|---|---|---|---|---|",
                f"| **Total Violations** | {tot['previous']} | {tot['current']} | {tot['diff']:+d} | **{tot['reduction_percent']}% reduction** |",
                f"| Errors | {err['previous']} | {err['current']} | {err['diff']:+d} | {err['reduction_percent']}% |",
                f"| Warnings | {warn['previous']} | {warn['current']} | {warn['diff']:+d} | {warn['reduction_percent']}% |",
                f"| Broken Links | {blk['previous']} | {blk['current']} | {blk['diff']:+d} | {blk['reduction_percent']}% |",
                f"| Stale Pages | {stl['previous']} | {stl['current']} | {stl['diff']:+d} | {stl['reduction_percent']}% |",
                "",
                "### Detailed rule reduction",
                "",
                "| Rule ID | Baseline | Current | Delta | Reduction |",
                "|---|---|---|---|---|",
            ]
        )
        for rd in comparison.get("rule_diffs", []):
            lines.append(
                f"| `{rd['rule_id']}` | {rd['previous']} | {rd['current']} | {rd['diff']:+d} | {rd['reduction_percent']}% |"
            )
        lines.append("")

    # Top 5 most violated rules
    top_5 = report_data.get("top_5_violated_rules", [])
    if top_5:
        lines.extend(
            [
                "## Top 5 most violated rules",
                "",
                "| Rank | Rule ID | Severity | Violation Count |",
                "|---|---|---|---|",
            ]
        )
        for idx, item in enumerate(top_5, start=1):
            lines.append(
                f"| {idx} | `{item['rule_id']}` | {item['severity']} | {item['count']} |"
            )
        lines.append("")

    # Stale pages detail
    stale_pages = report_data.get("stale_pages", [])
    if stale_pages:
        lines.extend(
            [
                "## Stale documentation pages",
                "",
                "| Document | Line | Warning Message |",
                "|---|---|---|",
            ]
        )
        for sp in stale_pages:
            lines.append(f"| `{sp['file']}` | L{sp['line']} | {sp['message']} |")
        lines.append("")

    # Broken links detail
    broken_links = report_data.get("broken_links", [])
    if broken_links:
        lines.extend(
            [
                "## Broken hyperlinks",
                "",
                "| Document | Line | Target URL | Failure Reason |",
                "|---|---|---|---|",
            ]
        )
        for bl in broken_links:
            lines.append(f"| `{bl['file']}` | L{bl['line']} | `{bl['url']}` | {bl['message']} |")
        lines.append("")

    return "\n".join(lines)
