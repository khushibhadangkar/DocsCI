"""Rule: Flag banned or condescending filler phrases."""

import re
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import mask_fenced_code, mask_inline_code

DEFAULT_BANNED = ["simply", "just", "easy", "obviously", "clearly", "basically"]


@register_rule
class BannedPhrasesRule(BaseRule):
    id: ClassVar[str] = "banned-phrases"
    description: ClassVar[str] = "Flag condescending or unnecessary filler words."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        cfg = context.config.rules.get(self.id)
        phrases = list(cfg.options.get("phrases", DEFAULT_BANNED)) if cfg else DEFAULT_BANNED
        pattern = re.compile(rf"\b({'|'.join(re.escape(p) for p in phrases)})\b", re.IGNORECASE)
        masked_body = mask_fenced_code(context.body)
        violations: list[Violation] = []

        for offset, raw_line in enumerate(masked_body.splitlines(), start=1):
            if not raw_line.strip() or raw_line.strip().startswith(("```", "~~~")):
                continue
            cleaned = mask_inline_code(raw_line)
            for m in pattern.finditer(cleaned):
                found = m.group(1)
                violations.append(
                    self.create_violation(
                        context, line=offset, column=m.start() + 1,
                        message=f"Banned word '{found}' weakens technical instructions.",
                        suggestion=f"Remove '{found}' and state the instruction directly.",
                    )
                )
        return violations
