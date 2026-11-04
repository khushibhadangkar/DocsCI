"""Rule: Warn when prose sentences exceed configured maximum word count."""

import re
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import is_table_line, mask_fenced_code, mask_inline_code


@register_rule
class MaxSentenceLengthRule(BaseRule):
    id: ClassVar[str] = "max-sentence-length"
    description: ClassVar[str] = "Sentences should not exceed the configured maximum word count."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        cfg = context.config.rules.get(self.id)
        max_words = int(cfg.options.get("max_words", 30)) if cfg else 30
        masked_body = mask_fenced_code(context.body)
        violations: list[Violation] = []
        for offset, raw_line in enumerate(masked_body.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith(("#", "```", "~~~", "---", ">")) or is_table_line(line):
                continue
            cleaned = mask_inline_code(line)
            # Match sentences ending with period, exclamation, or question mark
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
            for s in sentences:
                words = s.split()
                if len(words) > max_words:
                    snippet = " ".join(words[:6]) + "..."
                    violations.append(
                        self.create_violation(
                            context, line=offset, column=1,
                            message=f"Sentence exceeds {max_words} words ({len(words)} words): '{snippet}'",
                            suggestion="Split into shorter, focused sentences.",
                        )
                    )
        return violations
