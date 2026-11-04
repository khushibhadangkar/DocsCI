"""DocsCI: Docs-as-code quality and release-note automation tool."""

from docsci.models import DocsCIConfig, Severity, Violation
from docsci.rules import BaseRule, register_rule

__version__ = "0.1.0"
__all__ = ["DocsCIConfig", "Severity", "Violation", "BaseRule", "register_rule", "__version__"]
