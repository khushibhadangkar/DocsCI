"""Rule: Detect passive-voice constructions using a clearly labeled heuristic."""

import re
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import is_table_line, mask_fenced_code, mask_inline_code

BE_VERBS = r"\b(?:am|is|are|was|were|be|been|being)\b"
# Matches regular -ed participles and common irregular participles
PAST_PARTICIPLE = r"\b(?:[a-z]+ed|written|chosen|taken|run|sent|done|built|held|kept|found|lost|seen|set)\b"
PASSIVE_PATTERN = re.compile(rf"({BE_VERBS}\s+(?:\w+\s+)?{PAST_PARTICIPLE})", re.IGNORECASE)


@register_rule
class PassiveVoiceRule(BaseRule):
    id: ClassVar[str] = "passive-voice"
    description: ClassVar[str] = "Detect passive voice constructions (heuristic)."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        masked_body = mask_fenced_code(context.body)
        violations: list[Violation] = []
        for offset, raw_line in enumerate(masked_body.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith(("#", "```", "~~~", "---")) or is_table_line(line):
                continue
            cleaned = mask_inline_code(line)
            for match in PASSIVE_PATTERN.finditer(cleaned):
                phrase = match.group(1)
                violations.append(
                    self.create_violation(
                        context, line=offset, column=match.start() + 1,
                        message=f"Passive voice detected (heuristic): '{phrase}'.",
                        suggestion="Rewrite in active voice specifying who or what performs the action.",
                    )
                )
        return violations
