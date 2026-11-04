"""Internal and external hyperlink validation engine."""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from docsci.models import LinkConfig, LinkResult, LinkStatus
from docsci.utils.markdown_parser import extract_headings, mask_fenced_code, slugify_heading

logger = logging.getLogger(__name__)

# Matches [link text](url) or [link text](<url>)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((<[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Matches reference definitions: [ref]: url
REF_LINK_PATTERN = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)")
# Matches HTML anchor tags: <a href="url">
HTML_LINK_PATTERN = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)
HTML_ANCHOR_DEF_PATTERN = re.compile(r'<a\s+[^>]*(?:id|name)=["\']([^"\']+)["\']', re.IGNORECASE)


class LinkChecker:
    """Validates internal file/anchor links and external HTTP links."""

    def __init__(self, config: LinkConfig | None = None) -> None:
        self.config = config or LinkConfig()
        # In-memory cache for external links: url -> (status, code, elapsed, message)
        self._external_cache: dict[str, tuple[LinkStatus, int | None, float, str]] = {}
        # Cache for file headings/anchors: file_path -> set of anchor slugs
        self._anchor_cache: dict[Path, set[str]] = {}

    def extract_links_from_file(self, file_path: Path) -> list[tuple[int, str]]:
        """Extract list of (line_number, url) from markdown file, ignoring fenced code blocks."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to read file %s for links: %s", file_path, exc)
            return []

        masked_content = mask_fenced_code(content)
        links: list[tuple[int, str]] = []

        for line_idx, raw_line in enumerate(masked_content.splitlines(), start=1):
            line = raw_line.strip()
            # Standard markdown links [text](url)
            for m in MARKDOWN_LINK_PATTERN.finditer(line):
                url = m.group(2).strip("<>")
                links.append((line_idx, url))

            # Reference style links
            ref_match = REF_LINK_PATTERN.match(line)
            if ref_match:
                links.append((line_idx, ref_match.group(2)))

            # HTML links
            for m in HTML_LINK_PATTERN.finditer(line):
                links.append((line_idx, m.group(1)))

        return links

    def get_file_anchors(self, file_path: Path) -> set[str]:
        """Extract all valid anchor slugs and HTML anchor IDs from a markdown file."""
        resolved = file_path.resolve()
        if resolved in self._anchor_cache:
            return self._anchor_cache[resolved]

        anchors: set[str] = set()
        if not file_path.is_file():
            self._anchor_cache[resolved] = anchors
            return anchors

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return anchors

        lines = content.splitlines()
        headings = extract_headings(lines)
        for _, _, text in headings:
            slug = slugify_heading(text)
            if slug:
                anchors.add(slug)

        # Also extract <a id="..."> and <a name="...">
        for m in HTML_ANCHOR_DEF_PATTERN.finditer(content):
            anchors.add(m.group(1))

        self._anchor_cache[resolved] = anchors
        return anchors

    def check_internal_link(self, source_file: Path, line: int, link: str) -> LinkResult:
        """Validate an internal file path and/or anchor."""
        start_time = time.monotonic()

        # Handle intra-page anchor link e.g. #section-heading
        if link.startswith("#"):
            anchor = link.lstrip("#")
            valid_anchors = self.get_file_anchors(source_file)
            elapsed = time.monotonic() - start_time
            if not anchor or anchor in valid_anchors:
                return LinkResult(
                    file_path=source_file,
                    line=line,
                    url=link,
                    is_external=False,
                    status=LinkStatus.OK,
                    elapsed_seconds=elapsed,
                    message="Valid local anchor",
                )
            return LinkResult(
                file_path=source_file,
                line=line,
                url=link,
                is_external=False,
                status=LinkStatus.BROKEN,
                elapsed_seconds=elapsed,
                message=f"Local anchor '#{anchor}' not found in document.",
            )

        # Split path and possible anchor: path/to/doc.md#anchor
        parts = link.split("#", 1)
        file_part = parts[0]
        anchor_part = parts[1] if len(parts) > 1 else None

        # Resolve relative target file
        target_path = (source_file.parent / file_part).resolve()
        elapsed = time.monotonic() - start_time

        if not target_path.exists():
            return LinkResult(
                file_path=source_file,
                line=line,
                url=link,
                is_external=False,
                status=LinkStatus.BROKEN,
                elapsed_seconds=elapsed,
                message=f"Linked file '{file_part}' does not exist.",
            )

        if anchor_part:
            valid_anchors = self.get_file_anchors(target_path)
            if anchor_part not in valid_anchors:
                return LinkResult(
                    file_path=source_file,
                    line=line,
                    url=link,
                    is_external=False,
                    status=LinkStatus.BROKEN,
                    elapsed_seconds=elapsed,
                    message=f"Anchor '#{anchor_part}' not found in '{file_part}'.",
                )

        return LinkResult(
            file_path=source_file,
            line=line,
            url=link,
            is_external=False,
            status=LinkStatus.OK,
            elapsed_seconds=elapsed,
            message="Internal link target verified",
        )

    def is_allowlisted(self, url: str) -> bool:
        """Check if an external URL matches any configured allowlist pattern."""
        for pattern in self.config.allowlist:
            if url.startswith(pattern):
                return True
        return False

    def check_external_link(self, source_file: Path, line: int, url: str) -> LinkResult:
        """Validate external HTTP/HTTPS link with timeout, retries, and caching."""
        if self.is_allowlisted(url):
            return LinkResult(
                file_path=source_file,
                line=line,
                url=url,
                is_external=True,
                status=LinkStatus.OK,
                status_code=200,
                elapsed_seconds=0.0,
                message="Allowlisted URL",
            )

        # Check cache
        if url in self._external_cache:
            status, code, elapsed, msg = self._external_cache[url]
            return LinkResult(
                file_path=source_file,
                line=line,
                url=url,
                is_external=True,
                status=status,
                status_code=code,
                elapsed_seconds=elapsed,
                message=f"{msg} (cached)",
            )

        # Polite rate limit delay
        if self.config.rate_limit_delay_seconds > 0:
            time.sleep(self.config.rate_limit_delay_seconds)

        status, code, elapsed, message = self._fetch_url_with_retry(url)
        self._external_cache[url] = (status, code, elapsed, message)

        return LinkResult(
            file_path=source_file,
            line=line,
            url=url,
            is_external=True,
            status=status,
            status_code=code,
            elapsed_seconds=elapsed,
            message=message,
        )

    def _fetch_url_with_retry(self, url: str) -> tuple[LinkStatus, int | None, float, str]:
        """Perform HTTP request with retries and timeout."""
        attempts = 0
        max_attempts = max(1, self.config.retries + 1)
        headers = {
            "User-Agent": "DocsCI-LinkChecker/0.1 (+https://github.com/docsci/docsci)"
        }

        start_time = time.monotonic()
        last_error_msg = ""
        last_status_code: int | None = None

        while attempts < max_attempts:
            attempts += 1
            try:
                # Try HEAD first for efficiency, fallback to GET if HEAD disallowed
                req = urllib.request.Request(url, headers=headers, method="HEAD")
                try:
                    with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                        elapsed = time.monotonic() - start_time
                        code = resp.status
                        if elapsed > self.config.slow_threshold_seconds:
                            return LinkStatus.SLOW, code, elapsed, f"Slow response ({round(elapsed, 2)}s)"
                        return LinkStatus.OK, code, elapsed, "HTTP 200 OK"
                except urllib.error.HTTPError as he:
                    if he.code in (405, 403, 501):
                        # Some servers reject HEAD requests; retry with GET
                        req_get = urllib.request.Request(url, headers=headers, method="GET")
                        with urllib.request.urlopen(req_get, timeout=self.config.timeout_seconds) as resp_get:
                            elapsed = time.monotonic() - start_time
                            code = resp_get.status
                            if elapsed > self.config.slow_threshold_seconds:
                                return LinkStatus.SLOW, code, elapsed, f"Slow response ({round(elapsed, 2)}s)"
                            return LinkStatus.OK, code, elapsed, "HTTP 200 OK"
                    elif 300 <= he.code < 400:
                        elapsed = time.monotonic() - start_time
                        redirect_url = he.headers.get("Location", "")
                        return LinkStatus.REDIRECTED, he.code, elapsed, f"Redirected to {redirect_url}"
                    else:
                        last_status_code = he.code
                        last_error_msg = f"HTTP {he.code} {he.reason}"
                except urllib.error.URLError as ue:
                    last_error_msg = f"Network error: {ue.reason}"
            except Exception as exc:
                last_error_msg = f"Request failed: {exc}"

            # Short backoff before retry if not last attempt
            if attempts < max_attempts:
                time.sleep(0.2 * attempts)

        elapsed = time.monotonic() - start_time
        return LinkStatus.BROKEN, last_status_code, elapsed, last_error_msg

    def check_link(self, source_file: Path, line: int, url: str) -> LinkResult:
        """Route link check based on scheme."""
        stripped = url.strip()
        if stripped.startswith(("mailto:", "tel:", "javascript:")):
            return LinkResult(
                file_path=source_file,
                line=line,
                url=url,
                is_external=False,
                status=LinkStatus.SKIPPED,
                message="Skipped non-HTTP protocol",
            )

        if stripped.startswith(("http://", "https://")):
            return self.check_external_link(source_file, line, stripped)

        return self.check_internal_link(source_file, line, stripped)

    def check_file(self, file_path: Path) -> list[LinkResult]:
        """Check all links extracted from a single file."""
        links = self.extract_links_from_file(file_path)
        return [self.check_link(file_path, line, url) for line, url in links]

    def check_path(self, target: Path) -> tuple[list[LinkResult], int]:
        """Check all links across markdown files in target path."""
        from docsci.linter import collect_markdown_files

        files = collect_markdown_files(target)
        all_results: list[LinkResult] = []
        for f in files:
            all_results.extend(self.check_file(f))
        return all_results, len(files)


def format_link_table_report(
    results: list[LinkResult],
    scanned_files_count: int,
    base_dir: Path | None = None,
) -> str:
    """Format link check results as a human-readable ANSI table."""
    from docsci.utils.terminal import BOLD, CYAN, DIM, GREEN, RED, RESET, WHITE, YELLOW

    lines: list[str] = []
    lines.append("")
    lines.append(f"{BOLD}DocsCI Link Integrity Report{RESET}")
    lines.append("=" * 80)

    broken = [r for r in results if r.status == LinkStatus.BROKEN]
    slow = [r for r in results if r.status == LinkStatus.SLOW]
    redirected = [r for r in results if r.status == LinkStatus.REDIRECTED]
    ok_count = sum(1 for r in results if r.status == LinkStatus.OK)

    if not results:
        lines.append(f"{GREEN}✔ No links found in {scanned_files_count} file(s).{RESET}\n")
        return "\n".join(lines)

    if not broken and not slow and not redirected:
        lines.append(
            f"{GREEN}✔ All {len(results)} link(s) across {scanned_files_count} file(s) are valid and healthy.{RESET}\n"
        )
        return "\n".join(lines)

    # Group by file
    files_map: dict[str, list[LinkResult]] = {}
    for r in results:
        display_path = str(r.file_path)
        if base_dir:
            try:
                display_path = str(r.file_path.relative_to(base_dir))
            except ValueError:
                display_path = str(r.file_path)
        files_map.setdefault(display_path, []).append(r)

    for file_str, file_links in files_map.items():
        # Only show files with non-OK links or summaries
        interesting = [r for r in file_links if r.status != LinkStatus.OK]
        if not interesting:
            continue

        lines.append(f"\n{BOLD}{CYAN}📄 {file_str}{RESET} ({len(interesting)} issue(s)):")
        for r in interesting:
            if r.status == LinkStatus.BROKEN:
                badge = f"{RED}[BROKEN  ]{RESET}"
            elif r.status == LinkStatus.SLOW:
                badge = f"{YELLOW}[SLOW    ]{RESET}"
            elif r.status == LinkStatus.REDIRECTED:
                badge = f"{WHITE}[REDIRECT]{RESET}"
            else:
                badge = f"{GREEN}[OK      ]{RESET}"

            loc = f"L{r.line}".ljust(6)
            timing = f"({round(r.elapsed_seconds, 2)}s)"
            lines.append(f"  {badge} {loc} {r.url} {timing}")
            lines.append(f"            {DIM}↳ {r.message}{RESET}")

    lines.append("")
    lines.append("-" * 80)
    summary_text = (
        f"{BOLD}Summary:{RESET} Checked {len(results)} links across {scanned_files_count} files | "
        f"{RED}{len(broken)} broken{RESET} | "
        f"{YELLOW}{len(slow)} slow{RESET} | "
        f"{len(redirected)} redirected | "
        f"{GREEN}{ok_count} ok{RESET}"
    )
    lines.append(summary_text)
    lines.append("")
    return "\n".join(lines)


def format_link_json_report(results: list[LinkResult], scanned_files_count: int) -> str:
    """Format link check results as JSON."""
    report_data = {
        "summary": {
            "scanned_files": scanned_files_count,
            "total_links": len(results),
            "broken": sum(1 for r in results if r.status == LinkStatus.BROKEN),
            "slow": sum(1 for r in results if r.status == LinkStatus.SLOW),
            "redirected": sum(1 for r in results if r.status == LinkStatus.REDIRECTED),
            "ok": sum(1 for r in results if r.status == LinkStatus.OK),
        },
        "links": [r.to_dict() for r in results],
    }
    return json.dumps(report_data, indent=2)


def format_link_github_annotations(results: list[LinkResult], scanned_files_count: int) -> str:
    """Format link issues as GitHub Actions annotations."""
    lines: list[str] = []
    for r in results:
        if r.status == LinkStatus.BROKEN:
            lines.append(
                f"::error file={r.file_path},line={r.line},title=Broken Link::"
                f"Broken link '{r.url}': {r.message}"
            )
        elif r.status in (LinkStatus.SLOW, LinkStatus.REDIRECTED):
            lines.append(
                f"::warning file={r.file_path},line={r.line},title={r.status.value.capitalize()} Link::"
                f"{r.status.value.capitalize()} link '{r.url}': {r.message}"
            )

    lines.append(
        f"::notice::DocsCI link check scanned {len(results)} links in {scanned_files_count} files: "
        f"{sum(1 for r in results if r.status == LinkStatus.BROKEN)} broken."
    )
    return "\n".join(lines)
