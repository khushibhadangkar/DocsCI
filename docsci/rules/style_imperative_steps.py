"""Rule: Enforce that numbered procedure steps start with an imperative verb."""

import re
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule
from docsci.utils.markdown_parser import mask_fenced_code

STEP_PATTERN = re.compile(r"^\s*\d+\.\s+([A-Za-z]+)")
IMPERATIVE_VERBS = {
    "add", "apply", "assign", "attach", "browse", "check", "choose", "click", "clone",
    "configure", "confirm", "connect", "copy", "create", "delete", "deploy", "disable",
    "disconnect", "download", "enable", "ensure", "enter", "execute", "export", "find",
    "follow", "generate", "import", "inspect", "install", "locate", "navigate", "note",
    "open", "paste", "press", "reboot", "remove", "repeat", "restart", "restore", "review",
    "run", "save", "select", "send", "set", "specify", "start", "stop", "switch", "test",
    "type", "update", "upload", "verify", "view", "wait",
}


@register_rule
class ImperativeStepsRule(BaseRule):
    id: ClassVar[str] = "imperative-steps"
    description: ClassVar[str] = "Numbered procedure steps must begin with an imperative verb."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        masked_body = mask_fenced_code(context.body)
        violations: list[Violation] = []
        for offset, raw_line in enumerate(masked_body.splitlines(), start=1):
            match = STEP_PATTERN.match(raw_line)
            if not match:
                continue
            first_word = match.group(1)
            if first_word.lower() not in IMPERATIVE_VERBS:
                violations.append(
                    self.create_violation(
                        context, line=offset, column=match.start(1) + 1,
                        message=f"Numbered step starts with '{first_word}' instead of an imperative verb.",
                        suggestion="Begin step with an action verb (e.g., 'Select', 'Click', 'Run', 'Configure').",
                    )
                )
        return violations
