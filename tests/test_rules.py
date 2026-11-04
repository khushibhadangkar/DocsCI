"""Comprehensive unit tests for all DocsCI linting rules."""

from __future__ import annotations

from datetime import date, timedelta

from docsci.models import DocsCIConfig, Severity, TermDefinition
from docsci.rules.metadata import (
    FrontMatterDateRule,
    FrontMatterRequiredRule,
    StaleContentRule,
)
from docsci.rules.style_banned_phrases import BannedPhrasesRule
from docsci.rules.style_heading_hierarchy import HeadingHierarchyRule
from docsci.rules.style_imperative_steps import ImperativeStepsRule
from docsci.rules.style_passive_voice import PassiveVoiceRule
from docsci.rules.style_sentence_case import SentenceCaseHeadingRule
from docsci.rules.style_sentence_length import MaxSentenceLengthRule
from docsci.rules.style_single_h1 import SingleH1Rule
from docsci.rules.terminology import TerminologyRule


# 1. Heading Hierarchy
def test_heading_hierarchy_pass(make_context) -> None:
    content = "# Title\n\n## Section\n\n### Sub-section\n\n## Next Section"
    ctx = make_context(content)
    rule = HeadingHierarchyRule()
    assert rule.run(ctx) == []


def test_heading_hierarchy_fail(make_context) -> None:
    content = "# Title\n\n### Skipped to H3"
    ctx = make_context(content)
    rule = HeadingHierarchyRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "skipped from H1 to H3" in violations[0].message
    assert violations[0].severity == Severity.ERROR


# 2. Single H1
def test_single_h1_pass(make_context) -> None:
    content = "# Document Title\n\n## Section One\n\n## Section Two"
    ctx = make_context(content)
    rule = SingleH1Rule()
    assert rule.run(ctx) == []


def test_single_h1_fail(make_context) -> None:
    content = "# Document Title\n\n# Second Top Level Heading"
    ctx = make_context(content)
    rule = SingleH1Rule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Duplicate H1 heading" in violations[0].message
    assert violations[0].line == 3


# 3. Sentence Case Headings
def test_sentence_case_pass(make_context) -> None:
    content = "# Configure your backup storage\n\n## Connect to AWS S3"
    ctx = make_context(content)
    rule = SentenceCaseHeadingRule()
    assert rule.run(ctx) == []


def test_sentence_case_fail(make_context) -> None:
    content = "# Configure Your Backup Storage Today"
    ctx = make_context(content)
    rule = SentenceCaseHeadingRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "appears to use title case" in violations[0].message


# 4. Max Sentence Length
def test_max_sentence_length_pass(make_context) -> None:
    content = "This is a concise, well-crafted technical sentence. It is brief."
    ctx = make_context(content)
    rule = MaxSentenceLengthRule()
    assert rule.run(ctx) == []


def test_max_sentence_length_fail(make_context) -> None:
    long_sentence = " ".join(["word"] * 35) + "."
    ctx = make_context(long_sentence)
    rule = MaxSentenceLengthRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "exceeds 30 words" in violations[0].message


def test_max_sentence_length_ignores_code_and_tables(make_context) -> None:
    content = (
        "| " + " | ".join(["column_header"] * 35) + " |\n"
        "```python\n" + " ".join(["variable_name"] * 40) + "\n```\n"
    )
    ctx = make_context(content)
    rule = MaxSentenceLengthRule()
    assert rule.run(ctx) == []


# 5. Passive Voice
def test_passive_voice_pass(make_context) -> None:
    content = "The storage agent creates a full snapshot of the volume."
    ctx = make_context(content)
    rule = PassiveVoiceRule()
    assert rule.run(ctx) == []


def test_passive_voice_fail(make_context) -> None:
    content = "A full snapshot was created by the backup agent."
    ctx = make_context(content)
    rule = PassiveVoiceRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Passive voice detected (heuristic)" in violations[0].message


# 6. Banned Phrases
def test_banned_phrases_pass(make_context) -> None:
    content = "Run the setup command to configure the repository."
    ctx = make_context(content)
    rule = BannedPhrasesRule()
    assert rule.run(ctx) == []


def test_banned_phrases_fail(make_context) -> None:
    content = "Simply run the setup command, it is easy and obviously fast."
    ctx = make_context(content)
    rule = BannedPhrasesRule()
    violations = rule.run(ctx)
    assert len(violations) >= 3
    found_words = [v.message.lower() for v in violations]
    assert any("simply" in m for m in found_words)
    assert any("easy" in m for m in found_words)
    assert any("obviously" in m for m in found_words)


def test_banned_phrases_ignores_code(make_context) -> None:
    content = "```bash\ncurl -s https://example.com/simply-run.sh\n```\nUse `just` in code."
    ctx = make_context(content)
    rule = BannedPhrasesRule()
    assert rule.run(ctx) == []


# 7. Imperative Steps
def test_imperative_steps_pass(make_context) -> None:
    content = "1. Select the repository.\n2. Click Save.\n3. Verify the status."
    ctx = make_context(content)
    rule = ImperativeStepsRule()
    assert rule.run(ctx) == []


def test_imperative_steps_fail(make_context) -> None:
    content = "1. Selecting the repository is required.\n2. The user must click Save."
    ctx = make_context(content)
    rule = ImperativeStepsRule()
    violations = rule.run(ctx)
    assert len(violations) == 2
    assert "Selecting" in violations[0].message
    assert "The" in violations[1].message


# 8. Terminology
def test_terminology_pass(make_context) -> None:
    content = "Schedule a backup job for the database repository."
    cfg = DocsCIConfig(
        terminology=[
            TermDefinition(
                preferred="backup job",
                forbidden=["backup task", "backup routine"],
                explanation="Use 'backup job' for scheduled tasks.",
            )
        ]
    )
    ctx = make_context(content, config=cfg)
    rule = TerminologyRule()
    assert rule.run(ctx) == []


def test_terminology_fail(make_context) -> None:
    content = "Configure the backup task to run nightly."
    cfg = DocsCIConfig(
        terminology=[
            TermDefinition(
                preferred="backup job",
                forbidden=["backup task", "backup routine"],
                explanation="Use 'backup job' for scheduled tasks.",
            )
        ]
    )
    ctx = make_context(content, config=cfg)
    rule = TerminologyRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Forbidden term variant 'backup task' found" in violations[0].message
    assert "Replace with preferred term 'backup job'" in violations[0].suggestion


# 9. Metadata & Front Matter
def test_front_matter_required_pass(make_context) -> None:
    fm = {
        "title": "Topic Title",
        "description": "Topic description",
        "product_version": "1.0",
        "last_reviewed": "2026-11-04",
        "owner": "docs-team",
    }
    ctx = make_context("# Title", front_matter=fm)
    rule = FrontMatterRequiredRule()
    assert rule.run(ctx) == []


def test_front_matter_required_missing_fields(make_context) -> None:
    fm = {"title": "Topic Title"}
    ctx = make_context("# Title", front_matter=fm)
    rule = FrontMatterRequiredRule()
    violations = rule.run(ctx)
    assert len(violations) == 4
    fields_flagged = [v.message for v in violations]
    assert any("description" in m for m in fields_flagged)
    assert any("owner" in m for m in fields_flagged)


def test_front_matter_missing_entirely(make_context) -> None:
    ctx = make_context("# Title without front matter", front_matter={})
    rule = FrontMatterRequiredRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Missing YAML front matter block" in violations[0].message


def test_front_matter_malformed(make_context) -> None:
    ctx = make_context("# Title", front_matter={"_malformed": True})
    rule = FrontMatterRequiredRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Malformed YAML front matter" in violations[0].message


def test_front_matter_date_valid(make_context) -> None:
    fm = {"last_reviewed": "2026-11-04"}
    ctx = make_context("# Content", front_matter=fm)
    rule = FrontMatterDateRule()
    assert rule.run(ctx) == []


def test_front_matter_date_invalid_format(make_context) -> None:
    fm = {"last_reviewed": "11/04/2026"}
    ctx = make_context("# Content", front_matter=fm)
    rule = FrontMatterDateRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Invalid date format" in violations[0].message


def test_front_matter_date_invalid_calendar(make_context) -> None:
    fm = {"last_reviewed": "2026-02-31"}
    ctx = make_context("# Content", front_matter=fm)
    rule = FrontMatterDateRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "Calendar date '2026-02-31' is invalid" in violations[0].message


def test_stale_content_recent(make_context) -> None:
    recent = (date.today() - timedelta(days=30)).isoformat()
    fm = {"last_reviewed": recent}
    ctx = make_context("# Content", front_matter=fm)
    rule = StaleContentRule()
    assert rule.run(ctx) == []


def test_stale_content_expired(make_context) -> None:
    old = (date.today() - timedelta(days=200)).isoformat()
    fm = {"last_reviewed": old}
    ctx = make_context("# Content", front_matter=fm)
    rule = StaleContentRule()
    violations = rule.run(ctx)
    assert len(violations) == 1
    assert "exceeds 180 day threshold" in violations[0].message
