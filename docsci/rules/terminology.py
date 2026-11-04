"""Rule: Enforce preferred terminology and flag forbidden variants."""

import re
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import mask_fenced_code, mask_inline_code


@register_rule
class TerminologyRule(BaseRule):
    id: ClassVar[str] = "terminology-preferred"
    description: ClassVar[str] = "Enforce approved terminology and flag forbidden variants."
    default_severity: ClassVar[Severity] = Severity.ERROR

    def run(self, context: RuleContext) -> list[Violation]:
        if not context.terminology:
            return []
        violations: list[Violation] = []
        masked_body = mask_fenced_code(context.body)
        lines = masked_body.splitlines()

        for term in context.terminology:
            for forbidden in term.forbidden:
                pattern = re.compile(rf"\b{re.escape(forbidden)}\b", re.IGNORECASE)
                for offset, raw_line in enumerate(lines, start=1):
                    cleaned = mask_inline_code(raw_line)
                    for m in pattern.finditer(cleaned):
                        matched_text = m.group(0)
                        expl = f" {term.explanation}" if term.explanation else ""
                        violations.append(
                            self.create_violation(
                                context, line=offset, column=m.start() + 1,
                                message=f"Forbidden term variant '{matched_text}' found.{expl}",
                                suggestion=f"Replace with preferred term '{term.preferred}'.",
                            )
                        )
        return violations
