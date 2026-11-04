"""Pluggable linting rule architecture and registry for DocsCI."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from abc import ABC, abstractmethod
from typing import ClassVar

from docsci.models import DocsCIConfig, RuleContext, Severity, Violation

logger = logging.getLogger(__name__)


class BaseRule(ABC):
    """Abstract base class for all pluggable linting rules.

    Each concrete rule must define an `id`, `description`, and implement `run()`.
    Adding a new rule requires under 20 lines of code.
    """

    id: ClassVar[str] = ""
    description: ClassVar[str] = ""
    default_severity: ClassVar[Severity] = Severity.WARNING

    def __init__(self, severity: Severity | None = None) -> None:
        self.severity = severity or self.default_severity

    @abstractmethod
    def run(self, context: RuleContext) -> list[Violation]:
        """Execute the rule against the document context and return violations."""
        raise NotImplementedError

    def create_violation(
        self,
        context: RuleContext,
        line: int,
        column: int,
        message: str,
        suggestion: str | None = None,
        severity: Severity | None = None,
    ) -> Violation:
        """Helper to construct a consistent Violation instance."""
        return Violation(
            rule_id=self.id,
            file_path=context.file_path,
            line=line,
            column=column,
            message=message,
            severity=severity or self.severity,
            suggestion=suggestion,
        )


class RuleRegistry:
    """Central registry and auto-discovery manager for DocsCI rules."""

    _rules: ClassVar[dict[str, type[BaseRule]]] = {}
    _discovered: ClassVar[bool] = False

    @classmethod
    def register(cls, rule_cls: type[BaseRule]) -> type[BaseRule]:
        """Register a rule class. Can be used as a decorator."""
        if not rule_cls.id:
            raise ValueError(f"Rule class {rule_cls.__name__} must define a non-empty 'id'.")
        cls._rules[rule_cls.id] = rule_cls
        return rule_cls

    @classmethod
    def get(cls, rule_id: str) -> type[BaseRule] | None:
        """Retrieve a registered rule class by its ID."""
        cls.discover_rules()
        return cls._rules.get(rule_id)

    @classmethod
    def all_rules(cls) -> dict[str, type[BaseRule]]:
        """Return all registered rule classes."""
        cls.discover_rules()
        return dict(cls._rules)

    @classmethod
    def clear(cls) -> None:
        """Clear registered rules (mainly for isolated testing)."""
        cls._rules.clear()
        cls._discovered = False

    @classmethod
    def discover_rules(cls, package_name: str = "docsci.rules") -> None:
        """Automatically discover and import all rule modules in the given package."""
        if cls._discovered:
            return

        try:
            pkg = importlib.import_module(package_name)
        except ImportError as exc:
            logger.debug("Could not import rule package %s: %s", package_name, exc)
            return

        # Iterate through all modules in the package
        if hasattr(pkg, "__path__"):
            for _, mod_name, _ in pkgutil.iter_modules(pkg.__path__):
                full_mod_name = f"{package_name}.{mod_name}"
                try:
                    mod = importlib.import_module(full_mod_name)
                    # Scan for subclasses of BaseRule
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseRule)
                            and attr is not BaseRule
                            and attr.id
                        ):
                            cls._rules[attr.id] = attr
                except Exception as exc:
                    logger.warning("Failed to load rule module %s: %s", full_mod_name, exc)

        cls._discovered = True

    @classmethod
    def get_configured_rules(cls, config: DocsCIConfig) -> list[BaseRule]:
        """Instantiate all enabled rules configured for a DocsCI run."""
        cls.discover_rules()
        active_rules: list[BaseRule] = []

        for rule_id, rule_cls in cls._rules.items():
            rule_cfg = config.rules.get(rule_id)
            if rule_cfg is not None:
                if not rule_cfg.enabled:
                    continue
                active_rules.append(rule_cls(severity=rule_cfg.severity))
            else:
                # Enabled by default with default severity
                active_rules.append(rule_cls())

        return active_rules


def register_rule(cls: type[BaseRule]) -> type[BaseRule]:
    """Decorator to register a rule class."""
    return RuleRegistry.register(cls)
