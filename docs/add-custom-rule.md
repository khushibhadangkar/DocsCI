---
title: Adding a custom rule
description: Step-by-step tutorial to author and register a custom linting rule
product_version: '0.1.0'
last_reviewed: '2026-11-04'
owner: docs-team
---

# Adding a custom rule

Extend DocsCI by creating a custom rule in under twenty lines of code.

## Architecture

DocsCI discovers rules dynamically. Any Python class inheriting from `BaseRule` inside `docsci/rules/` registers automatically when the application starts.

## Step-by-step example

This tested example creates a rule that flags unexpanded "WORM" abbreviations in documentation body text.

### 1. Create the rule file

Create a new file named `docsci/rules/style_no_raw_worm.py`:

```python
from typing import ClassVar
from docsci.models import RuleContext, Severity, Violation
from docsci.rules import BaseRule, register_rule

@register_rule
class NoRawWormRule(BaseRule):
    id: ClassVar[str] = "no-raw-worm"
    description: ClassVar[str] = "Spell out Write Once Read Many or use immutable storage."
    default_severity: ClassVar[Severity] = Severity.WARNING

    def run(self, context: RuleContext) -> list[Violation]:
        violations: list[Violation] = []
        for line_num, line in enumerate(context.lines, start=1):
            if " WORM " in line:
                violations.append(
                    self.create_violation(
                        context, line=line_num, column=line.index("WORM") + 1,
                        message="Spell out 'Write Once, Read Many' or use 'immutable storage'.",
                        suggestion="Replace 'WORM' with 'immutable storage'.",
                    )
                )
        return violations
```

### 2. Configure the rule

Enable the rule in `docsci.yml`:

```yaml
rules:
  no-raw-worm:
    enabled: true
    severity: warning
```

### 3. Verify your rule

Run the linter to verify that the rule executes:

```bash
docsci lint docs/
```
