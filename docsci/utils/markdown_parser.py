"""Markdown parsing, code-block masking, and AST helper utilities."""

from __future__ import annotations

import re
from typing import Any

import yaml

# Regex patterns
FRONT_MATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
FENCED_CODE_PATTERN = re.compile(r"(```[a-zA-Z0-9_-]*\n)(.*?)(\n```)", re.DOTALL)
TILDE_CODE_PATTERN = re.compile(r"(~~~[a-zA-Z0-9_-]*\n)(.*?)(\n~~~)", re.DOTALL)
HTML_COMMENT_PATTERN = re.compile(r"<!--(.*?)-->", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")


def parse_front_matter(content: str) -> tuple[dict[str, Any], str, int]:
    """Extract YAML front matter, remaining body, and line count of front matter."""
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        return {}, content, 0

    fm_raw = match.group(1)
    full_match = match.group(0)
    line_count = full_match.count("\n")
    body = content[len(full_match) :]

    try:
        data = yaml.safe_load(fm_raw)
        if isinstance(data, dict):
            return data, body, line_count
        return {}, body, line_count
    except Exception:
        # Invalid YAML front matter
        return {"_malformed": True, "_raw": fm_raw}, body, line_count


def mask_fenced_code(content: str) -> str:
    """Mask fenced code blocks while preserving exact line counts.

    Replaces inner lines with empty lines so that line numbers match the original file.
    """

    def _replace_fence(m: re.Match[str]) -> str:
        open_fence = m.group(1)
        inner = m.group(2)
        close_fence = m.group(3)
        # Preserve newlines in inner code block
        blanked_inner = "\n" * inner.count("\n")
        return f"{open_fence}{blanked_inner}{close_fence}"

    masked = FENCED_CODE_PATTERN.sub(_replace_fence, content)
    masked = TILDE_CODE_PATTERN.sub(_replace_fence, masked)
    return masked


def mask_inline_code(line: str) -> str:
    """Replace inline code spans with space characters to preserve columns."""

    def _replace_inline(m: re.Match[str]) -> str:
        return " " * len(m.group(0))

    return INLINE_CODE_PATTERN.sub(_replace_inline, line)


def is_table_line(line: str) -> bool:
    """Check if a line is part of a markdown table."""
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def slugify_heading(text: str) -> str:
    """Generate a GitHub-compatible anchor slug from heading text."""
    # Strip markdown links e.g. [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Strip inline code ticks
    cleaned = cleaned.replace("`", "")
    # Lowercase
    cleaned = cleaned.lower()
    # Remove characters that are not alphanumeric, whitespace, or hyphens
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    # Convert whitespace to hyphens
    slug = re.sub(r"[\s_]+", "-", cleaned).strip("-")
    return slug


def extract_headings(content_lines: list[str]) -> list[tuple[int, int, str]]:
    """Extract list of (1-indexed line_num, level, text) for markdown headings.

    Lines inside fenced code blocks are ignored.
    """
    headings: list[tuple[int, int, str]] = []
    in_code_block = False

    for idx, line in enumerate(content_lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        match = HEADING_PATTERN.match(stripped)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append((idx, level, heading_text))

    return headings
