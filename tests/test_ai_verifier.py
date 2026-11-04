"""Unit tests for AI summarization, claim verification, and human accuracy gate."""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest
from typer.testing import CliRunner

from docsci.ai.client import (
    GeminiClient,
    MockLLMClient,
    get_llm_client,
    load_prompt_template,
)
from docsci.ai.verifier import (
    extract_keywords,
    generate_draft_markdown,
    split_into_claims,
    verify_claims,
)
from docsci.cli import app
from docsci.models import CommitEntry

runner = CliRunner()


@pytest.fixture
def sample_commits() -> list[CommitEntry]:
    return [
        CommitEntry(
            hash="111111111111",
            short_hash="1111111",
            author="Dev",
            date="2026-11-04",
            type="feat",
            scope="vault",
            description="Add immutable retention policies for S3 storage targets",
            breaking=False,
            pr="10",
        ),
        CommitEntry(
            hash="222222222222",
            short_hash="2222222",
            author="Dev",
            date="2026-11-04",
            type="fix",
            scope="recovery",
            description="Prevent file overwrite conflicts during point-in-time restore",
            breaking=False,
            pr="14",
        ),
    ]


def test_split_into_claims() -> None:
    text = (
        "### Key Highlights\n"
        "- Customers can now configure immutable retention policies on S3 repositories.\n"
        "- File restores no longer encounter overwrite conflicts.\n"
        "This release enhances enterprise backup resilience."
    )
    claims = split_into_claims(text)
    assert len(claims) == 3
    assert "immutable retention policies" in claims[0]
    assert "overwrite conflicts" in claims[1]
    assert "enterprise backup resilience" in claims[2]


def test_extract_keywords() -> None:
    words = extract_keywords("Add immutable retention policies for AWS S3!")
    assert "immutable" in words
    assert "retention" in words
    assert "policies" in words
    assert "for" not in words  # stop word


def test_verify_claims_supported(sample_commits: list[CommitEntry]) -> None:
    claims = [
        "Added immutable retention policies for S3 targets.",
        "Resolved file overwrite issues during restore operations.",
    ]
    verifications = verify_claims(claims, sample_commits)
    assert len(verifications) == 2
    assert verifications[0].status == "SUPPORTED"
    assert "1111111" in verifications[0].evidence_hashes
    assert verifications[1].status == "SUPPORTED"
    assert "2222222" in verifications[1].evidence_hashes


def test_verify_claims_unsupported_hallucination(sample_commits: list[CommitEntry]) -> None:
    claims = [
        "Added quantum-encrypted blockchain backup replication.",
        "Guaranteed zero-millisecond multi-region active database synchronization.",
    ]
    verifications = verify_claims(claims, sample_commits)
    assert len(verifications) == 2
    assert verifications[0].status == "UNSUPPORTED"
    assert verifications[0].evidence_hashes == []
    assert verifications[1].status == "UNSUPPORTED"


def test_generate_draft_markdown(sample_commits: list[CommitEntry]) -> None:
    claims = ["Added immutable retention policies for S3 storage targets."]
    verifications = verify_claims(claims, sample_commits)
    draft = generate_draft_markdown(
        summary_text="- Added immutable retention policies for S3 storage targets.",
        verifications=verifications,
        commits=sample_commits,
        prompt_version="v1.0.0",
        version_label="v2.0.0",
    )
    assert "> [!WARNING]" in draft
    assert "AI-assisted draft: requires human review." in draft
    assert "Prompt version: `v1.0.0`" in draft
    assert "Claim verification audit" in draft
    assert "✅ SUPPORTED" in draft


def test_generate_draft_markdown_with_unsupported_caution(sample_commits: list[CommitEntry]) -> None:
    claims = ["Invented unsupported feature claim."]
    verifications = verify_claims(claims, sample_commits)
    draft = generate_draft_markdown(
        summary_text="- Invented unsupported feature claim.",
        verifications=verifications,
        commits=sample_commits,
        prompt_version="v1.0.0",
        version_label="v2.0.0",
    )
    assert "> [!CAUTION]" in draft
    assert "UNSUPPORTED CLAIMS DETECTED" in draft
    assert "⚠️ UNSUPPORTED" in draft


def test_load_prompt_template(tmp_path: Path) -> None:
    p_file = tmp_path / "prompt.md"
    p_file.write_text("<!-- Prompt Version: v2.5.0 -->\nSummarize changes:\n{commits_list}")
    content, ver = load_prompt_template(p_file)
    assert ver == "v2.5.0"
    assert "{commits_list}" in content


def test_load_prompt_template_missing_fallback() -> None:
    content, ver = load_prompt_template("non_existent_prompt.md")
    assert ver == "default-v1"
    assert "{commits_list}" in content


def test_mock_llm_client(sample_commits: list[CommitEntry]) -> None:
    mock_clean = MockLLMClient()
    out_clean = mock_clean.generate_summary(sample_commits, "{commits_list}")
    assert "Notable Updates" in out_clean

    mock_hallucinating = MockLLMClient(inject_hallucination=True)
    out_hallucinated = mock_hallucinating.generate_summary(sample_commits, "{commits_list}")
    assert "quantum" in out_hallucinated.lower()


def test_gemini_client_missing_key() -> None:
    client = GeminiClient(api_key="")
    with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is not set"):
        client.generate_summary([], "prompt")


@patch("urllib.request.urlopen")
def test_gemini_client_successful_response(mock_urlopen: MagicMock, sample_commits: list[CommitEntry]) -> None:
    mock_resp = MagicMock()
    response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Customers can now configure immutable retention policies on S3."}]
                }
            }
        ]
    }
    mock_resp.read.return_value = json.dumps(response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = GeminiClient(api_key="test-api-key")
    result = client.generate_summary(sample_commits, "{commits_list}")
    assert "immutable retention policies on S3" in result


@patch("urllib.request.urlopen")
def test_gemini_client_http_error(mock_urlopen: MagicMock, sample_commits: list[CommitEntry]) -> None:
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://api.example.com",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=MagicMock(read=lambda: b'{"error": "Invalid API key"}'),
    )
    client = GeminiClient(api_key="test-api-key")
    with pytest.raises(RuntimeError, match="Gemini API returned HTTP 400"):
        client.generate_summary(sample_commits, "{commits_list}")


def test_get_llm_client_fallback() -> None:
    # When GEMINI_API_KEY is not set or force_mock is True, returns MockLLMClient
    with patch.dict("os.environ", {}, clear=True):
        client = get_llm_client()
        assert isinstance(client, MockLLMClient)


@pytest.fixture
def git_repo_for_ai(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "ai_repo"
    repo_dir.mkdir()
    repo = git.Repo.init(repo_dir)
    repo.config_writer().set_value("user", "name", "AI Tester").release()
    repo.config_writer().set_value("user", "email", "ai@example.com").release()

    f1 = repo_dir / "f.txt"
    f1.write_text("v1")
    repo.index.add([str(f1)])
    c1 = repo.index.commit("chore: init")
    repo.create_tag("v1.0.0", ref=c1)

    f1.write_text("v2")
    repo.index.add([str(f1)])
    c2 = repo.index.commit("feat(vault): add immutable backup retention policies (#5)")
    repo.create_tag("v1.1.0", ref=c2)

    return repo_dir


def test_cli_release_notes_ai_summary_supported(git_repo_for_ai: Path, tmp_path: Path) -> None:
    out_file = tmp_path / "DRAFT.md"
    result = runner.invoke(
        app,
        [
            "release-notes",
            "--repo",
            str(git_repo_for_ai),
            "--from",
            "v1.0.0",
            "--to",
            "v1.1.0",
            "--ai-summary",
            "--output",
            str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "AI-assisted draft: requires human review" in content
    assert "✅ SUPPORTED" in content


@patch("docsci.ai.client.get_llm_client")
def test_cli_release_notes_ai_summary_unsupported_gate(
    mock_get_client: MagicMock,
    git_repo_for_ai: Path,
    tmp_path: Path,
) -> None:
    # Mock LLM returns hallucinated claim
    mock_client = MockLLMClient(
        custom_response="- Added quantum encrypted cross-datacenter teleportation replication."
    )
    mock_get_client.return_value = mock_client

    out_file = tmp_path / "DRAFT_FAIL.md"
    result = runner.invoke(
        app,
        [
            "release-notes",
            "--repo",
            str(git_repo_for_ai),
            "--from",
            "v1.0.0",
            "--to",
            "v1.1.0",
            "--ai-summary",
            "--output",
            str(out_file),
        ],
    )
    # Human accuracy gate should FAIL (exit code 1)
    assert result.exit_code == 1
    assert "Human Accuracy Gate" in result.output
    assert "UNSUPPORTED" in result.output

    # When --allow-unsupported is passed, it should exit 0
    result_allowed = runner.invoke(
        app,
        [
            "release-notes",
            "--repo",
            str(git_repo_for_ai),
            "--from",
            "v1.0.0",
            "--to",
            "v1.1.0",
            "--ai-summary",
            "--allow-unsupported",
            "--output",
            str(out_file),
        ],
    )
    assert result_allowed.exit_code == 0
    assert "Proceeding despite unsupported claims" in result_allowed.output
