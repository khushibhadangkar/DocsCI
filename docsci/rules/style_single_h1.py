"""Rule: Enforce at most one H1 heading per document."""

from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import extract_headings


@register_rule
class SingleH1Rule(BaseRule):
    id: ClassVar[str] = "single-h1"
    description: ClassVar[str] = "Documents must have at most one H1 heading."
    default_severity: ClassVar[Severity] = Severity.ERROR

    def run(self, context: RuleContext) -> list[Violation]:
        h1s = [(line_idx, txt) for line_idx, lvl, txt in extract_headings(context.lines) if lvl == 1]
        if len(h1s) <= 1:
            return []
        first_line = h1s[0][0]
        return [
            self.create_violation(
                context,
                line=line,
                column=1,
                message=f"Duplicate H1 heading '{txt}'. Primary H1 defined at line {first_line}.",
                suggestion="Convert this heading to H2 or lower.",
            )
            for line, txt in h1s[1:]
        ]
