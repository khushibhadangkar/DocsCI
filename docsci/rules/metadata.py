"""Rules: Front matter metadata validation, date format, and stale content checks."""

import re
from datetime import date, datetime
from typing import ClassVar

from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule

DEFAULT_REQUIRED_FIELDS = ["title", "description", "product_version", "last_reviewed", "owner"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@register_rule
class FrontMatterRequiredRule(BaseRule):
    id: ClassVar[str] = "front-matter-required"
    description: ClassVar[str] = "Ensure required metadata fields exist in YAML front matter."
    default_severity: ClassVar[Severity] = Severity.ERROR

    def run(self, context: RuleContext) -> list[Violation]:
        if context.front_matter.get("_malformed"):
            return [
                self.create_violation(
                    context, line=1, column=1,
                    message="Malformed YAML front matter block.",
                    suggestion="Fix YAML syntax error between initial '---' markers.",
                )
            ]
        if not context.front_matter:
            return [
                self.create_violation(
                    context, line=1, column=1,
                    message="Missing YAML front matter block at top of document.",
                    suggestion="Add '---' block with title, description, product_version, last_reviewed, and owner.",
                )
            ]

        cfg = context.config.rules.get(self.id)
        required = list(cfg.options.get("required_fields", DEFAULT_REQUIRED_FIELDS)) if cfg else DEFAULT_REQUIRED_FIELDS
        violations: list[Violation] = []
        for field in required:
            val = context.front_matter.get(field)
            if val is None or str(val).strip() == "":
                violations.append(
                    self.create_violation(
                        context, line=1, column=1,
                        message=f"Missing required front matter field '{field}'.",
                        suggestion=f"Provide a non-empty value for '{field}: ...'",
                    )
                )
        return violations


@register_rule
class FrontMatterDateRule(BaseRule):
    id: ClassVar[str] = "front-matter-date"
    description: ClassVar[str] = "Validate that last_reviewed is a valid YYYY-MM-DD date."
    default_severity: ClassVar[Severity] = Severity.ERROR

    def run(self, context: RuleContext) -> list[Violation]:
        if not context.front_matter or "last_reviewed" not in context.front_matter:
            return []
        raw_val = context.front_matter["last_reviewed"]
        val_str = raw_val.isoformat() if isinstance(raw_val, (date, datetime)) else str(raw_val).strip()
        if not DATE_PATTERN.match(val_str):
            return [
                self.create_violation(
                    context, line=1, column=1,
                    message=f"Invalid date format '{val_str}' for last_reviewed. Expected YYYY-MM-DD.",
                    suggestion="Format date as YYYY-MM-DD (e.g., 2026-11-04).",
                )
            ]
        try:
            datetime.strptime(val_str, "%Y-%m-%d")
        except ValueError:
            return [
                self.create_violation(
                    context, line=1, column=1,
                    message=f"Calendar date '{val_str}' is invalid.",
                    suggestion="Provide a valid calendar date formatted as YYYY-MM-DD.",
                )
            ]
        return []


@register_rule
class StaleContentRule(BaseRule):
    id: ClassVar[str] = "stale-content"
    description: ClassVar[str] = "Warn when document last_reviewed date exceeds stale threshold."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        if not context.front_matter or "last_reviewed" not in context.front_matter:
            return []
        raw_val = context.front_matter["last_reviewed"]
        val_str = raw_val.isoformat() if isinstance(raw_val, (date, datetime)) else str(raw_val).strip()
        try:
            reviewed_date = datetime.strptime(val_str, "%Y-%m-%d").date()
        except ValueError:
            return []

        cfg = context.config.rules.get(self.id)
        stale_days = int(cfg.options.get("stale_days", 180)) if cfg else 180
        age_days = (date.today() - reviewed_date).days
        if age_days > stale_days:
            return [
                self.create_violation(
                    context, line=1, column=1,
                    message=f"Document last reviewed {age_days} days ago (exceeds {stale_days} day threshold).",
                    suggestion=f"Review and update document, then update last_reviewed to today ({date.today().isoformat()}).",
                )
            ]
        return []
