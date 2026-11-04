"""Tests for BaseRule and RuleRegistry auto-discovery mechanism."""

from __future__ import annotations

from typing import ClassVar

import pytest

from docsci.models import DocsCIConfig, RuleConfig, RuleContext, Severity, Violation
from docsci.rules import BaseRule, RuleRegistry


class DummyTestRule(BaseRule):
    id: ClassVar[str] = "dummy-test-rule"
    description: ClassVar[str] = "Rule for testing registry"
    default_severity: ClassVar[Severity] = Severity.INFO

    def run(self, context: RuleContext) -> list[Violation]:
        if "forbidden_dummy" in context.raw_content:
            return [
                self.create_violation(
                    context=context,
                    line=1,
                    column=1,
                    message="Found forbidden dummy text",
                    suggestion="Remove it",
                )
            ]
        return []


def test_rule_registration() -> None:
    RuleRegistry.register(DummyTestRule)
    retrieved = RuleRegistry.get("dummy-test-rule")
    assert retrieved is DummyTestRule


def test_rule_registration_empty_id() -> None:
    class BadRule(BaseRule):
        id: ClassVar[str] = ""
        description: ClassVar[str] = "Invalid"

        def run(self, context: RuleContext) -> list[Violation]:
            return []

    with pytest.raises(ValueError, match="must define a non-empty 'id'"):
        RuleRegistry.register(BadRule)


def test_rule_execution(make_context) -> None:
    rule = DummyTestRule()
    ctx_clean = make_context("Clean content")
    assert rule.run(ctx_clean) == []

    ctx_failing = make_context("forbidden_dummy text")
    violations = rule.run(ctx_failing)
    assert len(violations) == 1
    assert violations[0].rule_id == "dummy-test-rule"
    assert violations[0].severity == Severity.INFO
    assert violations[0].suggestion == "Remove it"


def test_rule_severity_override() -> None:
    rule = DummyTestRule(severity=Severity.ERROR)
    assert rule.severity == Severity.ERROR


def test_get_configured_rules_disabling() -> None:
    RuleRegistry.register(DummyTestRule)
    config = DocsCIConfig(
        rules={
            "dummy-test-rule": RuleConfig(enabled=False, severity=Severity.ERROR),
        }
    )
    active = RuleRegistry.get_configured_rules(config)
    dummy_instances = [r for r in active if r.id == "dummy-test-rule"]
    assert len(dummy_instances) == 0


def test_get_configured_rules_enabled_with_override() -> None:
    RuleRegistry.register(DummyTestRule)
    config = DocsCIConfig(
        rules={
            "dummy-test-rule": RuleConfig(enabled=True, severity=Severity.ERROR),
        }
    )
    active = RuleRegistry.get_configured_rules(config)
    dummy_instances = [r for r in active if r.id == "dummy-test-rule"]
    assert len(dummy_instances) == 1
    assert dummy_instances[0].severity == Severity.ERROR
