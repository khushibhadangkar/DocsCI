"""Rule: Enforce sentence-case headings."""

import re
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import extract_headings

LOWER_EXEMPT = {"a", "an", "the", "in", "on", "at", "to", "for", "with", "from", "by", "and", "or", "of"}


@register_rule
class SentenceCaseHeadingRule(BaseRule):
    id: ClassVar[str] = "sentence-case-heading"
    description: ClassVar[str] = "Headings should use sentence case rather than title case."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        violations: list[Violation] = []
        for line_num, _, text in extract_headings(context.lines):
            clean = re.sub(r"`[^`]+`", "", text)  # ignore inline code
            words = list(re.findall(r"\b[A-Za-z]+\b", clean))
            if len(words) < 2:
                continue
            # Check non-first words: flag if capitalized words that are not all-caps acronyms exist in title-case pattern
            subsequent = [w for w in words[1:] if w.lower() not in LOWER_EXEMPT]
            title_cased = [w for w in subsequent if w[0].isupper() and not w.isupper()]
            if len(title_cased) >= 2 or (len(subsequent) == 1 and len(title_cased) == 1):
                suggested = words[0].capitalize() + " " + " ".join(w.lower() if not w.isupper() else w for w in words[1:])
                violations.append(
                    self.create_violation(
                        context, line=line_num, column=1,
                        message=f"Heading '{text}' appears to use title case instead of sentence case.",
                        suggestion=f"Consider: '{suggested}'",
                    )
                )
        return violations
