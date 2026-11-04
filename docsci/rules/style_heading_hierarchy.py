"""Rule: Enforce heading hierarchy without skipped levels."""

from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import extract_headings


@register_rule
class HeadingHierarchyRule(BaseRule):
    id: ClassVar[str] = "heading-hierarchy"
    description: ClassVar[str] = "Heading levels must not skip increments (e.g., H1 to H3)."
    default_severity: ClassVar[Severity] = Severity.ERROR

    def run(self, context: RuleContext) -> list[Violation]:
        violations: list[Violation] = []
        headings = extract_headings(context.lines)
        prev_level = 0
        for line_num, level, text in headings:
            if prev_level > 0 and level > prev_level + 1:
                violations.append(
                    self.create_violation(
                        context,
                        line=line_num,
                        column=1,
                        message=f"Heading level skipped from H{prev_level} to H{level} for '{text}'.",
                        suggestion=f"Use H{prev_level + 1} instead of H{level}.",
                    )
                )
            prev_level = level
        return violations
