"""Pytest fixtures for DocsCI test suite."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from docsci.models import DocsCIConfig, RuleContext
from docsci.rules import RuleRegistry


@pytest.fixture(autouse=True)
def reset_rule_registry() -> Generator[None, None, None]:
    """Ensure rule registry is refreshed for tests."""
    yield
    RuleRegistry.clear()


@pytest.fixture
def sample_config() -> DocsCIConfig:
    """Fixture providing a default DocsCIConfig."""
    return DocsCIConfig()


@pytest.fixture
def make_context(sample_config: DocsCIConfig):
    """Factory fixture to create RuleContext instances."""

    def _factory(
        content: str,
        file_path: Path | None = None,
        front_matter: dict | None = None,
        config: DocsCIConfig | None = None,
    ) -> RuleContext:
        path = file_path or Path("docs/test-topic.md")
        fm = front_matter or {}
        cfg = config or sample_config
        lines = content.splitlines()
        return RuleContext(
            file_path=path,
            raw_content=content,
            front_matter=fm,
            body=content,
            lines=lines,
            config=cfg,
            terminology=cfg.terminology,
        )

    return _factory
