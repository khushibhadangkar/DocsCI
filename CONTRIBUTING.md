# Contributing to DocsCI

Thank you for contributing to DocsCI! We welcome contributions from developers, technical writers, and documentation engineers.

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/example/DocsCI.git
   cd DocsCI
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install DocsCI and development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Code Quality Standards

Before opening a pull request, ensure all linters, formatting, and tests pass:

```bash
# Check code style with Ruff
ruff check .

# Run pytest test suite with coverage
pytest --cov=docsci --cov-report=term-missing

# Lint the documentation itself
docsci lint docs/ --strict

# Check documentation links
docsci links docs/ --strict
```

The minimum required test coverage is **85%**.

## Adding a Custom Lint Rule

DocsCI rules are modular and pluggable. Adding a new rule takes less than 20 lines of code:

1. Create a new module in `docsci/rules/` (for example, `docsci/rules/style_custom.py`).
2. Subclass `BaseRule` and decorate it with `@register_rule`.
3. Define `id`, `description`, `default_severity`, and implement `run(self, context: RuleContext) -> list[Violation]`.
4. Add unit tests in `tests/test_rules.py`.

Review [Adding a Custom Rule](docs/add-custom-rule.md) for a tested tutorial.

## Commit Message Guidelines

DocsCI follows the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat`: New user-facing feature or rule
- `fix`: Bug fix in linter, links, or release notes
- `docs`: Documentation updates
- `test`: Test suite additions or updates
- `refactor`: Code reorganization without functional changes
- `chore`: Build or dependency maintenance
